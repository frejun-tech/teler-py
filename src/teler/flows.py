from typing import Any, Dict


class CallFlow:

    @staticmethod
    def dial(
        from_number: str,
        to_number: str,
        status_callback_url: str = "",
        record: bool = True,
    ) -> Dict[str, Any]:
        """
        Build and return dial action flow.
        """
        return {
            "action": "dial",
            "from_number": from_number,
            "to_number": to_number,
            "status_callback_url": status_callback_url,
            "record": record,
        }

    @staticmethod
    def stream(
        ws_url: str, chunk_size: int = 400, record: bool = True
    ) -> Dict[str, Any]:
        """
        Build and return stream action flow.
        """
        return {
            "action": "stream",
            "ws_url": ws_url,
            "chunk_size": chunk_size,
            "record": record,
        }

    @staticmethod
    def play(file_url: str) -> Dict[str, Any]:
        """
        Build and return play action flow.
        """
        return {"action": "play", "file_url": file_url}
