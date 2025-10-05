export type ReportSummary = {
  period: { from: string; to: string }
  tenant: string
  questions: number
  unique_users: number
  resolved_rate: number | null
  zero_hit_rate: number | null
  tokens: number
  cost_jpy: number
  top_docs: { id: string; name?: string; count: number }[]
}

export function buildClientReportEmail(s: ReportSummary): string {
  const pct = (v: number | null) =>
    v == null ? '-' : `${Math.round(v * 100)}%`
  const docs =
    (s.top_docs || [])
      .slice(0, 5)
      .map(d => `<li>${d.name ?? d.id}（${d.count}件）</li>`)
      .join('') || '<li>該当なし</li>'
  return `
  <div style="font-family:Inter,Arial,sans-serif; color:#1f2937; line-height:1.6;">
    <h2 style="margin:0 0 12px;">チャットボット レポート</h2>
    <div style="color:#6b7280;">期間: ${s.period.from} ～ ${
      s.period.to
    } ／ テナント: ${s.tenant}</div>
    <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0;" />
    <table cellpadding="0" cellspacing="0" style="width:100%;max-width:640px">
      <tr><td>総質問数</td><td align="right"><strong>${s.questions.toLocaleString()}</strong></td></tr>
      <tr><td>ユニーク利用者数（推定）</td><td align="right"><strong>${s.unique_users.toLocaleString()}</strong></td></tr>
      <tr><td>解決率</td><td align="right"><strong>${pct(
        s.resolved_rate
      )}</strong></td></tr>
      <tr><td>ゼロヒット率</td><td align="right"><strong>${pct(
        s.zero_hit_rate
      )}</strong></td></tr>
      <tr><td>推定コスト</td><td align="right"><strong>¥${Math.round(
        s.cost_jpy
      ).toLocaleString()}</strong></td></tr>
      <tr><td>総トークン</td><td align="right"><strong>${Math.round(
        s.tokens
      ).toLocaleString()}</strong></td></tr>
    </table>
    <div style="font-size:12px;color:#6b7280;margin-top:10px;">
      <div style="font-weight:600;margin:8px 0 4px;">項目の説明</div>
      <ul style="margin:0;padding-left:18px;">
        <li>総質問数: 対象期間の質問件数合計</li>
        <li>ユニーク利用者（推定）: 匿名IDに基づく近似ユニーク（延べユニーク）</li>
        <li>解決率: 「解決しましたか？」Yes ÷ (Yes + No)</li>
        <li>ゼロヒット率: 参照文書が0件だった割合</li>
        <li>推定コスト: モデル単価とトークン使用量に基づく概算（円）</li>
        <li>総トークン: 入力+出力トークンの合計（概算）</li>
      </ul>
    </div>
    <h3 style="margin:16px 0 8px;">上位参照ドキュメント</h3>
    <ul style="margin:0;padding-left:20px;">${docs}</ul>
    <p style="font-size:12px;color:#6b7280;margin-top:16px;">
      ※ 利用者数は匿名推定です。原文は保存していません（必要時のみマスキング済みスニペットを別途ご提供可能）。
    </p>
  </div>`
}
