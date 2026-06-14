import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { ResumesService } from "@/client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { Loader2, Upload, FileText, Calendar } from "lucide-react"

export const Route = createFileRoute("/_layout/resume")({
  component: ResumePage,
  head: () => ({
    meta: [
      {
        title: "Resumes - Job Applier",
      },
    ],
  }),
})

function ResumePage() {
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)

  const { data: resumes, isLoading } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => ResumesService.listResumes(),
  })

  const uploadMutation = useMutation({
    mutationFn: (uploadFile: File) => {
      return ResumesService.uploadResume({
        formData: {
          file: uploadFile,
        },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] })
      queryClient.invalidateQueries({ queryKey: ["profile"] })
      toast.success("Resume uploaded and parsed successfully!")
      setFile(null)
    },
    onError: (err: any) => {
      logger.error(err)
      toast.error(err.response?.data?.detail || "Failed to upload and parse resume.")
    }
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = () => {
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  return (
    <div className="flex flex-col gap-8 pb-12">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Resume Management</h1>
        <p className="text-muted-foreground">Upload resumes to parse skills, work history, and automatically populate your application profile.</p>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
        {/* Upload Card */}
        <Card className="md:col-span-1 shadow-md h-fit">
          <CardHeader>
            <CardTitle>Upload Resume</CardTitle>
            <CardDescription>Supported formats: PDF, TXT</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col items-center justify-center border-2 border-dashed border-muted-foreground/20 rounded-lg p-6 hover:bg-muted/50 transition-colors relative cursor-pointer">
              <input
                type="file"
                accept=".pdf,.txt,.md"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <Upload className="h-10 w-10 text-muted-foreground mb-2" />
              <p className="text-sm font-medium text-center">
                {file ? file.name : "Click to browse files"}
              </p>
              {file && (
                <p className="text-xs text-muted-foreground mt-1">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              )}
            </div>

            <Button
              onClick={handleUpload}
              className="w-full"
              disabled={!file || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Parsing resume...
                </>
              ) : (
                "Upload & Parse"
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Resumes List */}
        <Card className="md:col-span-2 shadow-md">
          <CardHeader>
            <CardTitle>Parsed Resumes</CardTitle>
            <CardDescription>Your uploaded documents available for job applications.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : resumes && resumes.length > 0 ? (
              <div className="divide-y">
                {resumes.map((resume) => (
                  <div key={resume.id} className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
                    <div className="flex items-center gap-3">
                      <div className="bg-primary/10 p-2.5 rounded-lg">
                        <FileText className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <p className="font-semibold">{resume.filename}</p>
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                          <Calendar className="h-3.5 w-3.5" />
                          <span>Uploaded on {new Date(resume.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No resumes uploaded yet.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
const logger = {
  error: (msg: any) => console.error(msg)
}
