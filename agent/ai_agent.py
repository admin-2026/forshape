"""
AI Agent orchestrator for multiple API providers.

This module provides an AI agent that orchestrates a list of Steps,
each of which can call tools to interact with the file system.

Supports multiple API providers: OpenAI, Fireworks, and more.
"""

from typing import TYPE_CHECKING, Optional

from .api_debugger import APIDebugger
from .api_provider import APIProvider, create_api_provider
from .chat_history_manager import ChatHistoryManager
from .edit_history import EditHistory
from .logger_protocol import LoggerProtocol
from .step import Step, StepResult
from .step_config import StepConfigRegistry

if TYPE_CHECKING:
    from .step_jump_controller import StepJumpController


class AIAgent:
    """
    AI Agent orchestrator for multiple API providers.

    This agent orchestrates a list of Steps, each of which can use tools
    to interact with the file system and perform tasks autonomously.
    """

    def __init__(
        self,
        api_key: Optional[str],
        model: str,
        steps: dict[str, Step],
        start_step: str,
        logger: LoggerProtocol,
        edit_history: EditHistory,
        history_manager: ChatHistoryManager,
        api_debugger: Optional[APIDebugger] = None,
        provider: str = "openai",
        provider_config=None,
        response_steps: list[str] = None,
        step_jump_controller: Optional["StepJumpController"] = None,
    ):
        """
        Initialize the AI agent.

        Args:
            api_key: API key for the selected provider
            model: Model identifier to use
            steps: Dict mapping step names to Step instances
            start_step: Name of the step to start execution from
            logger: LoggerProtocol instance for logging
            edit_history: EditHistory instance for tracking file changes
            history_manager: ChatHistoryManager instance for conversation history
            api_debugger: Optional APIDebugger instance for dumping API data
            provider: API provider to use ("openai", "fireworks", etc.)
            provider_config: Optional ProviderConfig instance for provider configuration
            response_steps: Optional list of step names whose responses will be collected for UI printing
            step_jump_controller: Optional StepJumpController for dynamic step flow control
        """
        if start_step not in steps:
            raise ValueError(f"start_step '{start_step}' not found in steps")
        self.logger = logger
        self.model = model
        self.steps = steps
        self.start_step = start_step
        self.history_manager = history_manager
        self.provider = self._initialize_provider(provider, api_key, provider_config)
        self.provider_name = provider
        self.last_token_usage = None
        self._cancellation_requested = False
        self.api_debugger = api_debugger
        self._conversation_counter = 0
        self.edit_history = edit_history
        self.response_steps = set(response_steps) if response_steps else set()
        self.step_jump_controller = step_jump_controller

    def _initialize_provider(
        self, provider_name: str, api_key: Optional[str], provider_config=None
    ) -> Optional[APIProvider]:
        """
        Initialize the API provider.

        Args:
            provider_name: Name of the provider ("openai", "fireworks", etc.)
            api_key: API key for authentication
            provider_config: Optional ProviderConfig instance for provider configuration

        Returns:
            APIProvider instance or None if initialization fails
        """
        if not api_key:
            return None

        try:
            from .api_provider import create_api_provider_from_config

            if provider_config:
                provider = create_api_provider_from_config(provider_config, api_key)
            else:
                provider = create_api_provider(provider_name, api_key)

            if not provider.is_available():
                print(f"Error: {provider_name} provider not available")
                return None

            return provider
        except ValueError as e:
            print(f"Error: {e}")
            return None
        except Exception as e:
            print(f"Error initializing {provider_name} provider: {e}")
            return None

    def _generate_conversation_id(self) -> str:
        """
        Generate a unique conversation ID.

        Returns:
            Unique conversation ID string
        """
        from datetime import datetime

        self._conversation_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"conv_{timestamp}_{self._conversation_counter:03d}"

    def process_request(
        self,
        user_input: str,
        step_configs: StepConfigRegistry,
        token_callback=None,
        step_response_callback=None,
    ) -> None:
        """
        Process the user's request through the AI agent.

        Args:
            user_input: The user's input message
            step_configs: Registry containing step-specific configurations
            token_callback: Optional callback function to receive token usage updates after each iteration
            step_response_callback: Optional callback function(step_name, response) called when a step in response_steps completes
        """
        if self.provider is None:
            raise RuntimeError(f"{self.provider_name} provider not initialized. Please check your API key.")

        # Clear any stale jump requests from previous conversations
        if self.step_jump_controller:
            self.step_jump_controller.clear()

        # Generate a new conversation ID for this user request
        conversation_id = self._generate_conversation_id()

        # Start new conversation on edit history
        self.edit_history.start_new_conversation(conversation_id, user_request=user_input)

        self.history_manager.set_conversation_id(conversation_id)
        self.logger.info(f"Started new conversation: {conversation_id}")

        self._agent_run(step_configs, token_callback, step_response_callback)

    def request_cancellation(self):
        """Request cancellation of the current AI processing."""
        self._cancellation_requested = True

    def reset_cancellation(self):
        """Reset the cancellation flag for new requests."""
        self._cancellation_requested = False

    def _is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancellation_requested

    def _agent_run(
        self,
        step_configs: StepConfigRegistry,
        token_callback=None,
        step_response_callback=None,
    ) -> None:
        """
        Run the agent by executing all steps in sequence.

        Args:
            step_configs: Registry containing step-specific configurations
            token_callback: Optional callback function to receive token usage updates
            step_response_callback: Optional callback function(step_name, response) called when a step in response_steps completes
        """
        if self.provider is None:
            raise RuntimeError(f"{self.provider_name} provider not initialized. Please check your API key.")

        if not self.steps:
            raise RuntimeError("No steps configured for this agent.")

        # Reset cancellation flag at the start of each run
        self.reset_cancellation()

        # Initialize cumulative token usage
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0

        # Execute steps using StepJump-based flow control
        current_step_name = self.start_step
        step_index = 0

        while current_step_name:
            step = self.steps[current_step_name]
            step_name = current_step_name
            step_index += 1
            self.logger.info(f"Executing step {step_index}: {step_name}")

            # Create a token callback that accumulates usage
            def step_token_callback(token_data, _step_name=step_name, _step_index=step_index):
                nonlocal total_prompt_tokens, total_completion_tokens, total_tokens
                total_prompt_tokens = token_data["prompt_tokens"]
                total_completion_tokens = token_data["completion_tokens"]
                total_tokens = token_data["total_tokens"]

                if token_callback:
                    token_callback(
                        {
                            "prompt_tokens": total_prompt_tokens,
                            "completion_tokens": total_completion_tokens,
                            "total_tokens": total_tokens,
                            "iteration": token_data.get("iteration", 0),
                            "step": _step_name,
                            "step_index": _step_index,
                        }
                    )

            # Get step-specific config from registry
            step_config = step_configs.get_config(step_name)
            step_initial_messages = step_configs.get_messages(step_name)

            # Get history for the current step
            history = self.history_manager.get_history()

            # Add user message to history
            if step_config:
                user_input = step_config.get_initial_message()
                if user_input:
                    self.history_manager.add_user_message(user_input, key=f"step_{step_index}_user")

            # Run the step
            result: StepResult = step.step_run(
                provider=self.provider,
                model=self.model,
                history=history,
                step_config=step_config,
                initial_messages=step_initial_messages,
                api_debugger=self.api_debugger,
                token_callback=step_token_callback,
                cancellation_check=self._is_cancelled,
                response_content_callback=step_response_callback if step_name in self.response_steps else None,
                step_jump_controller=self.step_jump_controller,
            )

            # Add history messages only if step actually completed (not call_pending)
            # For call_pending, we'll continue later and add history then
            if result.status != "call_pending":
                self.history_manager.add_history_messages(result.history_messages, step_name=step_name)

            # Accumulate token usage
            total_prompt_tokens += result.token_usage.get("prompt_tokens", 0)
            total_completion_tokens += result.token_usage.get("completion_tokens", 0)
            total_tokens += result.token_usage.get("total_tokens", 0)

            # If step was cancelled or errored, stop execution
            if result.status in ("cancelled", "error"):
                self.logger.info(f"Step {step_name} ended with status: {result.status}")
                if result.status == "error":
                    error_msg = result.history_messages[0].content if result.history_messages else "Unknown error"
                    raise RuntimeError(error_msg)
                break

            # Determine next step via StepJump
            if result.step_jump:
                current_step_name = result.step_jump.get_next_step(result)
            else:
                current_step_name = None

        # Store final token usage
        self.last_token_usage = {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
        }

    def clear_history(self):
        """Clear the conversation history."""
        self.history_manager.clear_history()

    def get_history_manager(self) -> ChatHistoryManager:
        """
        Get the ChatHistoryManager instance for advanced history operations.

        Returns:
            ChatHistoryManager instance
        """
        return self.history_manager

    def get_model(self) -> str:
        """
        Get the model identifier being used.

        Returns:
            Model identifier string
        """
        return self.model

    def set_model(self, model: str):
        """
        Set the model identifier to use for future requests.

        Args:
            model: Model identifier string
        """
        self.model = model
        self.logger.info(f"Model changed to: {model}")

    def get_last_token_usage(self) -> Optional[dict]:
        """
        Get the token usage data from the most recent request.

        Returns:
            Dict with 'prompt_tokens', 'completion_tokens', and 'total_tokens' keys,
            or None if no request has been made yet
        """
        return self.last_token_usage
