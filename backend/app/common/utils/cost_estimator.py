from dataclasses import dataclass


@dataclass
class CostMeta:
    model: str
    input_tokens: int
    output_tokens: int
    input_cost_jpy: float
    output_cost_jpy: float
    total_cost_jpy: float


def estimate_cost_jpy(model: str, input_tokens: int, output_tokens: int) -> CostMeta:
    """
    極めて簡易な概算。将来、実料金表と紐づける。
    """
    # 仮レート（例）: 1k tokens あたり 入力 ¥0.15 / 出力 ¥0.6
    in_rate = 0.15 / 1000.0
    out_rate = 0.60 / 1000.0
    input_cost = input_tokens * in_rate
    output_cost = output_tokens * out_rate
    total = input_cost + output_cost
    return CostMeta(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_jpy=round(input_cost, 6),
        output_cost_jpy=round(output_cost, 6),
        total_cost_jpy=round(total, 6),
    )
