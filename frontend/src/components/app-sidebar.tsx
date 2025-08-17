'use client'

import { useCallback, useEffect, useState } from 'react'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from '@/components/ui/sidebar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import {
  FileText,
  Settings,
  Brain,
  Zap,
  Thermometer,
  Hash,
  Upload,
  Trash2,
  CheckCircle,
} from 'lucide-react'
import { toast } from 'sonner'
import { config } from '@/lib/config'

export default function AppSidebar() {
  const [maxTokens, setMaxTokens] = useState([2048])
  const [streamingEnabled, setStreamingEnabled] = useState(true)
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [isVectorStoreReady, setIsVectorstoreReady] = useState(false)
  const [deleting, setDeleting] = useState<Record<string, boolean>>({})

  const syncFiles = useCallback(async () => {
    try {
      const response = await fetch('/api/file/documents', { cache: 'no-store' })
      if (!response.ok) {
        let detail = 'Unknown error'
        try {
          const err = await response.json()
          detail = err.error || err.detail || detail
        } catch {}
        throw new Error(detail)
      }

      const data = await response.json()
      const files: string[] = Array.isArray(data.files)
        ? data.files.map((f: any) => f.filename)
        : []

      setUploadedFiles(files)
      setIsVectorstoreReady((data.total_files ?? files.length) > 0)
    } catch (e) {
      console.error('sync files error:', e)
      toast.error(
        `ドキュメント一覧の再取得に失敗: ${e instanceof Error ? e.message : 'Unknown error'}`
      )
    }
  }, [])

  useEffect(() => {
    syncFiles()
  }, [syncFiles])

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    const validFiles = Array.from(files).filter(file => {
      const isValid =
        file.type === 'application/pdf' ||
        file.name.toLowerCase().endsWith('.pdf')
      if (!isValid) {
        toast.error(`${file.name}はPDFファイルではありません`)
      }
      return isValid
    })

    if (validFiles.length === 0) {
      toast.warning('有効なPDFファイルがありませんでした')
      event.target.value = ''
      return
    }

    setIsUploading(true)

    try {
      for (const file of validFiles) {
        console.log(`Uploading: ${file.name}`)

        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch(`/api/file/upload`, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Network response was not ok')
        }

        const result = await response.json()
        setUploadedFiles(prev => [...prev, file.name])
        toast.success(`${file.name}をアップロードしました`)
      }

      setIsVectorstoreReady(true)
      await syncFiles()
    } catch (error) {
      console.error('Upload error:', error)
      toast.error(
        error instanceof Error ? error.message : 'アップロードに失敗しました'
      )
    } finally {
      setIsUploading(false)
      event.target.value = ''
    }
  }

  const removeFile = async (fileName: string) => {
    if (!confirm(`${fileName}を削除しますか？`)) return

    setDeleting(prev => {
      const next = { ...prev }
      next[fileName] = true
      return next
    })

    try {
      const response = await fetch('/api/file/delete', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileName }),
      })

      if (!response.ok) {
        let detail = 'Unknown error'
        try {
          const err = await response.json()
          detail = err.error || err.detail || detail
        } catch {}
        if (response.status === 404) {
          toast.info(`${fileName}は既に存在しません`)
          setUploadedFiles(prev => prev.filter(f => f !== fileName))
          setIsVectorstoreReady(false)
          return
        }
        throw new Error(detail)
      }

      const result = await response.json()
      setUploadedFiles(prev => prev.filter(file => file !== fileName))
      setIsVectorstoreReady(result.remaining_files > 0)
      toast.success(`${result.deleted_filename ?? fileName}を削除しました`)
      await syncFiles()
    } catch (error) {
      console.error('delete error:', error)
      toast.error(
        error instanceof Error ? error.message : 'ファイル削除に失敗しました'
      )
    } finally {
      setDeleting(prev => {
        const next = { ...prev }
        delete next[fileName]
        return next
      })
    }
  }

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-1">
          <Brain className="h-6 w-6" />
          <span className="font-semibold">AI Assistant</span>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {/* PDF Upload Section */}
        <SidebarGroup>
          <SidebarGroupLabel className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            PDF Documents
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Upload PDFs</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-center w-full">
                  <label
                    className={`flex flex-col items-center justify-center w-full h-12 border-2 border-dashed rounded-lg cursor-pointer transition-colors border-muted-foreground/25 hover:bg-muted/50 
                      ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="flex gap-2 items-center justify-center">
                      {isUploading ? (
                        <>
                          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                          <p className="text-xs text-muted-foreground text-center">
                            アップロード中...
                          </p>
                        </>
                      ) : (
                        <>
                          <Upload className="h-4 w-4 text-muted-foreground" />
                          <p className="text-xs text-muted-foreground text-center">
                            Click to upload PDFs
                          </p>
                        </>
                      )}
                    </div>
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf"
                      multiple
                      onChange={handleFileUpload}
                      disabled={isUploading}
                    />
                  </label>
                </div>
                {isVectorStoreReady ? (
                  <div className="flex gap-2 items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <p className="text-xs text-green-600 text-center font-medium">
                      ベクトルストア準備完了
                    </p>
                  </div>
                ) : (
                  ''
                )}
                {uploadedFiles.length > 0 && (
                  <div className="space-y-2">
                    <Label className="text-xs font-medium">Upload Files:</Label>
                    {uploadedFiles.map((fileName, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-2 bg-muted rounded-md"
                      >
                        <span className="text-xs truncate flex-1">
                          {fileName}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(fileName)}
                          className="h-6 w-6 p-0"
                          disabled={Boolean(deleting[fileName])}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        {/* LLM Setting */}
        <SidebarGroup>
          <SidebarGroupLabel className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            LLM Settings
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <Card>
              <CardContent className="space-y-4">
                {/* Max Tokens */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium flex items-center gap-1">
                      <Hash className="h-3 w-3" />
                      Max Tokens
                    </Label>
                    <span className="text-xs text-muted-foreground">
                      {maxTokens[0]}
                    </span>
                  </div>
                  <Slider
                    value={maxTokens}
                    onValueChange={setMaxTokens}
                    max={4096}
                    min={256}
                    step={256}
                    className="w-full"
                  />
                </div>

                {/* Streaming */}
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    Streaming
                  </Label>
                  <Switch
                    checked={streamingEnabled}
                    onCheckedChange={setStreamingEnabled}
                  />
                </div>
              </CardContent>
            </Card>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        {/* Quick Actions */}
        <SidebarGroup>
          <SidebarGroupLabel>Quick Actions</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton>
                  <FileText className="h-4 w-4" />
                  <span>Clear Chat History</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton>
                  <Settings className="h-4 w-4" />
                  <span>Export Settings</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div className="p-2">
          <div className="text-xs text-muted-foreground text-center">
            Tuukaa RAG Chatbot
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
