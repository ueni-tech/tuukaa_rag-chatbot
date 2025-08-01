import Link from 'next/link'
import { config } from '@/lib/config'

export default function Home() {
  return (
    <>
      <Link href={config.apiUrl}>ヘルスチェック</Link>
    </>
  )
}
