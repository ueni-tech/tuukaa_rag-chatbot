'use client'

import { useState } from 'react'
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
  const [model, setModel] = useState('gpt-4o-mini')
  const [temperture, setTemperture] = useState([0.7])
  const [maxTokens, setMaxTokens] = useState([2048])
  const [streamingEnabled, setStreamingEnabled] = useState(true)
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [isVectorStoreReady, setIsVectorstoreReady] = useState(false)

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

        const response = await fetch('/api/upload', {
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

  const removeFile = (fileName: string) => {
    setUploadedFiles(prev => prev.filter(file => file !== fileName))
    if (uploadedFiles.length <= 1) {
      setIsVectorstoreReady(false)
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
                    className={`flex flex-col items-center justify-center w-full h-24 border-2 border-dashed rounded-lg cursor-pointer transition-colors
                      ${
                        isVectorStoreReady
                          ? 'border-green-500/50 bg-green-50/50 dark:bg-green-950/20'
                          : 'border-muted-foreground/25 hover:bg-muted/50'
                      }
                      ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      {isUploading ? (
                        <>
                          <div className="h-6 w-6 mb-2 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                          <p className="text-xs text-muted-foreground text-center">
                            アップロード中...
                          </p>
                        </>
                      ) : isVectorStoreReady ? (
                        <>
                          <CheckCircle className="h-6 w-6 mb-2 text-green-600" />
                          <p className="text-xs text-green-600 text-center font-medium">
                            ベクトルストア準備完了
                          </p>
                        </>
                      ) : (
                        <>
                          <Upload className="h-6 w-6 mb-2 text-muted-foreground" />
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
              <CardContent className="space-y-4 pt-4">
                {/* Model Selection */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Model</Label>
                  <Select value={model} onValueChange={setModel}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-4o-mini">gpt-4o-mini</SelectItem>
                      <SelectItem value="gpt-4.1-nano">gpt-4.1-nano</SelectItem>
                      <SelectItem value="gpt-4.1-mini">gpt-4.1-mini</SelectItem>
                      <SelectItem value="gpt-4o">gpt-4o</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {/* Temperature */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium flex items-center gap-1">
                      <Thermometer className="h-3 w-3" />
                      Tempereture
                    </Label>
                    <span className="text-xs text-muted-foreground">
                      {temperture[0]}
                    </span>
                  </div>
                  <Slider
                    value={temperture}
                    onValueChange={setTemperture}
                    max={2}
                    min={0}
                    step={0.1}
                    className="w-full"
                  />
                </div>

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
