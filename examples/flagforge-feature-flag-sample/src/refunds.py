from typing import Protocol


class FlagsmithClient(Protocol):
    def has_feature(self, key: str) -> bool: ...


def refund_action(flagsmith: FlagsmithClient) -> str:
    if flagsmith.has_feature("instant_refunds"):
        return "queue-for-review"
    return "manual-review"
