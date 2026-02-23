class Boolean2D:
    @staticmethod
    def union(face_a, face_b):
        """
        Return the union of two 2D faces.

        Args:
            face_a: Part.Face
            face_b: Part.Face

        Returns:
            Part.Shape
        """
        return face_a.fuse(face_b)

    @staticmethod
    def intersection(face_a, face_b):
        """
        Return the intersection of two 2D faces.

        Args:
            face_a: Part.Face
            face_b: Part.Face

        Returns:
            Part.Shape
        """
        return face_a.common(face_b)

    @staticmethod
    def difference(face_a, face_b):
        """
        Return face_a minus face_b.

        Args:
            face_a: Part.Face
            face_b: Part.Face

        Returns:
            Part.Shape
        """
        return face_a.cut(face_b)
