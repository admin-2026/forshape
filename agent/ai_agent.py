"""
AI Agent orchestrator for multiple API providers.

This module provides an AI agent that orchestrates a list of Steps,
each of which can call tools to interact with the file system.

Supports multiple API providers: OpenAI, Fireworks, and more.
"""

from typing import Optional

from .api_debugger import APIDebugger
from .api_provider import APIProvider, create_api_provider
from .chat_history_manager import ChatHistoryManager
from .edit_history import EditHistory
from .logger_protocol import LoggerProtocol
from .step import Step, StepResult
from .step_config import StepConfigRegistry


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
        steps: list[Step],
        logger: LoggerProtocol,
        edit_history: EditHistory,
        api_debugger: Optional[APIDebugger] = None,
        provider: str = "openai",
        provider_config=None,
    ):
        """
        Initialize the AI agent.

        Args:
            api_key: API key for the selected provider
            model: Model identifier to use
            steps: List of Step instances to execute
            logger: LoggerProtocol instance for logging
            edit_history: EditHistory instance for tracking file changes
            api_debugger: Optional APIDebugger instance for dumping API data
            provider: API provider to use ("openai", "fireworks", etc.)
            provider_config: Optional ProviderConfig instance for provider configuration
        """
        self.logger = logger
        self.model = model
        self.steps = steps
        self.history_manager = ChatHistoryManager(max_messages=None)
        self.provider = self._initialize_provider(provider, api_key, provider_config)
        self.provider_name = provider
        self.last_token_usage = None
        self._cancellation_requested = False
        self.api_debugger = api_debugger
        self._conversation_counter = 0
        self.edit_history = edit_history

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

    def process_request(self, user_input: str, step_configs: StepConfigRegistry, token_callback=None) -> str:
        """
        Process the user's request through the AI agent.

        Args:
            user_input: The user's input message
            step_configs: Registry containing step-specific configurations
            token_callback: Optional callback function to receive token usage updates after each iteration

        Returns:
            AI response string
        """
        if self.provider is None:
            return f"Error: {self.provider_name} provider not initialized. Please check your API key."

        try:
            # Generate a new conversation ID for this user request
            conversation_id = self._generate_conversation_id()

            # Start new conversation on edit history
            self.edit_history.start_new_conversation(conversation_id, user_request=user_input)

            self.history_manager.set_conversation_id(conversation_id)
            self.logger.info(f"Started new conversation: {conversation_id}")

            response = self._agent_run(step_configs, token_callback)
            return response

        except Exception as e:
            error_msg = f"Error processing AI request: {str(e)}"
            return error_msg

    def request_cancellation(self):
        """Request cancellation of the current AI processing."""
        self._cancellation_requested = True

    def reset_cancellation(self):
        """Reset the cancellation flag for new requests."""
        self._cancellation_requested = False

    def _is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancellation_requested

    def _agent_run(self, step_configs: StepConfigRegistry, token_callback=None) -> str:
        """
        Run the agent by executing all steps in sequence.

        Args:
            step_configs: Registry containing step-specific configurations
            token_callback: Optional callback function to receive token usage updates

        Returns:
            Final response from the last step
        """
        if self.provider is None:
            return f"Error: {self.provider_name} provider not initialized. Please check your API key."

        if not self.steps:
            return "Error: No steps configured for this agent."

        # Reset cancellation flag at the start of each run
        self.reset_cancellation()

        # Initialize cumulative token usage
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0

        # Track the final result
        final_response = ""

        # Execute each step in sequence
        for i, step in enumerate(self.steps):
            self.logger.info(f"Executing step {i + 1}/{len(self.steps)}: {step.name}")

            # Create a token callback that accumulates usage
            def step_token_callback(token_data):
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
                            "step": step.name,
                            "step_index": i + 1,
                        }
                    )

            # Get step-specific config from registry
            step_input_queue = step_configs.get_input_queue(step.name)
            step_initial_messages = step_configs.get_messages(step.name)

            # Get history for the current step
            history = self.history_manager.get_history()

            # Add user message to history
            if step_input_queue:
                user_input = step_input_queue.get_initial_message()
                if user_input:
                    self.history_manager.add_user_message(user_input)

            # Run the step
            result: StepResult = step.step_run(
                provider=self.provider,
                model=self.model,
                history=history,
                input_queue=step_input_queue,
                initial_messages=step_initial_messages,
                api_debugger=self.api_debugger,
                token_callback=step_token_callback,
                cancellation_check=self._is_cancelled,
            )

            final_response = result.response

            # Accumulate token usage
            total_prompt_tokens += result.token_usage.get("prompt_tokens", 0)
            total_completion_tokens += result.token_usage.get("completion_tokens", 0)
            total_tokens += result.token_usage.get("total_tokens", 0)

            # If step was cancelled or errored, stop execution
            if result.status in ("cancelled", "error"):
                self.logger.info(f"Step {step.name} ended with status: {result.status}")
                break

            # Update history with final response, pass response to next step
            self.history_manager.add_assistant_message(final_response)

        # Store final token usage
        self.last_token_usage = {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
        }

        return final_response

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
