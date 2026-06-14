import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { ApplicationsService } from "@/client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
import { Loader2, Briefcase, Play, HelpCircle, Eye, CheckCircle2, AlertTriangle, XCircle, Clock } from "lucide-react"

export const Route = createFileRoute("/_layout/applications")({
  component: ApplicationsPage,
  head: () => ({
    meta: [
      {
        title: "Applications - Job Applier",
      },
    ],
  }),
})

function ApplicationsPage() {
  const queryClient = useQueryClient()
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null)
  const [isResolverOpen, setIsResolverOpen] = useState(false)
  const [isTimelineOpen, setIsTimelineOpen] = useState(false)
  const [answers, setAnswers] = useState<Record<string, string>>({})

  // Fetch applications
  const { data: apps, isLoading } = useQuery({
    queryKey: ["applications"],
    queryFn: () => ApplicationsService.listApplications(),
    refetchInterval: 5000, // Poll every 5s to show live crawler progress
  })

  // Fetch fields for selected application
  const { data: fields } = useQuery({
    queryKey: ["fields", selectedAppId],
    queryFn: () => (selectedAppId ? ApplicationsService.getApplicationFields({ appId: selectedAppId }) : Promise.resolve([])) as Promise<any>,
    enabled: !!selectedAppId,
  })

  // Fetch events for selected application
  const { data: events } = useQuery({
    queryKey: ["events", selectedAppId],
    queryFn: () => (selectedAppId ? ApplicationsService.getApplicationEvents({ appId: selectedAppId }) : Promise.resolve([])) as Promise<any>,
    enabled: !!selectedAppId,
    refetchInterval: 3000,
  })

  const appList = (apps || []) as any[]
  const fieldList = (fields || []) as any[]
  const eventList = (events || []) as any[]

  // Start automation
  const startMutation = useMutation({
    mutationFn: (appId: string) => ApplicationsService.startApplying({ appId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] })
      toast.success("Application process started!")
    }
  })

  // Submit resolved fields mutation
  const resolveMutation = useMutation({
    mutationFn: async ({ appId, answersList }: { appId: string, answersList: any[] }) => {
      // 1. Save responses
      await ApplicationsService.resolveApplicationFields({
        appId,
        requestBody: answersList
      })
      // 2. Submit application
      return ApplicationsService.submitJobApplication({ appId })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] })
      toast.success("Answers submitted and application resumed successfully!")
      setIsResolverOpen(false)
      setAnswers({})
    },
    onError: () => {
      toast.error("Failed to submit answers.")
    }
  })

  // Submit ready application
  const submitMutation = useMutation({
    mutationFn: (appId: string) => ApplicationsService.submitJobApplication({ appId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] })
      toast.success("Application submission started!")
    }
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SUBMITTED":
        return <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20 border-green-500/20 flex items-center gap-1 w-fit"><CheckCircle2 className="h-3 w-3" /> Submitted</Badge>
      case "WAITING_FOR_USER":
        return <Badge className="bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 border-amber-500/20 flex items-center gap-1 w-fit"><HelpCircle className="h-3 w-3" /> Action Required</Badge>
      case "IN_PROGRESS":
        return <Badge className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 border-blue-500/20 flex items-center gap-1 w-fit"><Loader2 className="h-3 w-3 animate-spin" /> In Progress</Badge>
      case "READY_TO_SUBMIT":
        return <Badge className="bg-purple-500/10 text-purple-500 hover:bg-purple-500/20 border-purple-500/20 flex items-center gap-1 w-fit"><CheckCircle2 className="h-3 w-3" /> Ready to Submit</Badge>
      case "FAILED":
        return <Badge className="bg-rose-500/10 text-rose-500 hover:bg-rose-500/20 border-rose-500/20 flex items-center gap-1 w-fit"><XCircle className="h-3 w-3" /> Failed</Badge>
      default:
        return <Badge className="bg-muted text-muted-foreground flex items-center gap-1 w-fit"><Clock className="h-3 w-3" /> Draft</Badge>
    }
  }

  const openResolver = (appId: string) => {
    setSelectedAppId(appId)
    setIsResolverOpen(true)
    setAnswers({})
  }

  const openTimeline = (appId: string) => {
    setSelectedAppId(appId)
    setIsTimelineOpen(true)
  }

  const handleResolveSubmit = () => {
    if (!selectedAppId || !fieldList) return
    
    // Construct answers body
    const unresolvedFields = fieldList.filter(f => !f.resolved || !f.value)
    const answersList = unresolvedFields.map(f => ({
      field_id: f.id,
      value: answers[f.id] || ""
    }))

    // Validate that required fields are filled
    const missingRequired = unresolvedFields.some(f => f.is_required && !answers[f.id])
    if (missingRequired) {
      toast.error("Please answer all required questions.")
      return
    }

    resolveMutation.mutate({ appId: selectedAppId, answersList })
  }

  return (
    <div className="flex flex-col gap-8 pb-12">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Applications Tracking</h1>
        <p className="text-muted-foreground">Monitor the browser crawler actions, resolve missing questions, and view submission statuses.</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-24">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </div>
      ) : appList && appList.length > 0 ? (
        <div className="grid grid-cols-1 gap-6">
          {appList.map((app) => (
            <Card key={app.id} className="shadow-sm hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <div>
                  <CardTitle className="text-lg font-bold flex items-center gap-2">
                    <Briefcase className="h-5 w-5 text-primary shrink-0" />
                    {app.job.title}
                  </CardTitle>
                  <CardDescription className="font-semibold text-sm mt-0.5">
                    {app.job.company} — {app.job.location}
                  </CardDescription>
                </div>
                {getStatusBadge(app.status)}
              </CardHeader>
              <CardContent className="flex justify-between items-center pt-2 border-t mt-2">
                <div className="text-xs text-muted-foreground">
                  Updated {new Date(app.updated_at).toLocaleTimeString()}
                </div>
                <div className="flex gap-2">
                  <Button onClick={() => openTimeline(app.id)} variant="outline" size="sm">
                    <Eye className="mr-1.5 h-4 w-4" /> View Logs
                  </Button>

                  {app.status === "DRAFT" && (
                    <Button onClick={() => startMutation.mutate(app.id)} disabled={startMutation.isPending} size="sm">
                      <Play className="mr-1.5 h-4 w-4" /> Start Applying
                    </Button>
                  )}

                  {app.status === "WAITING_FOR_USER" && (
                    <Button onClick={() => openResolver(app.id)} variant="secondary" size="sm" className="bg-amber-500 hover:bg-amber-600 text-white border-0">
                      <HelpCircle className="mr-1.5 h-4 w-4" /> Answer Questions
                    </Button>
                  )}

                  {app.status === "READY_TO_SUBMIT" && (
                    <Button onClick={() => submitMutation.mutate(app.id)} disabled={submitMutation.isPending} size="sm">
                      <CheckCircle2 className="mr-1.5 h-4 w-4" /> Submit Application
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-24 text-muted-foreground border-2 border-dashed rounded-lg">
          <Briefcase className="h-16 w-16 mx-auto mb-4 opacity-20" />
          <h3 className="text-lg font-bold">No applications started</h3>
          <p className="text-sm mt-1">Visit the Jobs board and click Apply to start an application.</p>
        </div>
      )}

      {/* Timeline Logs Dialog */}
      <Dialog open={isTimelineOpen} onOpenChange={setIsTimelineOpen}>
        <DialogContent className="max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Automation Activity Log</DialogTitle>
            <DialogDescription>Live action stream from the Playwright runner.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {eventList && eventList.length > 0 ? (
              <div className="relative border-l pl-4 space-y-4">
                {eventList.map((event) => (
                  <div key={event.id} className="relative">
                    <span className="absolute -left-[21px] mt-1.5 h-3.5 w-3.5 rounded-full border-2 border-background bg-primary" />
                    <div className="text-xs text-muted-foreground">
                      {new Date(event.created_at).toLocaleTimeString()}
                    </div>
                    <div className="text-sm font-medium mt-0.5">{event.message}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-6">No runner logs yet.</p>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Question Resolver Dialog */}
      <Dialog open={isResolverOpen} onOpenChange={setIsResolverOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Resolve Application Questions
            </DialogTitle>
            <DialogDescription>
              We encountered questions on the application form we couldn't resolve automatically. Complete these to resume.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4 max-h-[50vh] overflow-y-auto pr-2">
            {fieldList && fieldList.filter(f => !f.resolved || !f.value).map((field) => (
              <div key={field.id} className="space-y-1.5 border-b pb-4 last:border-b-0 last:pb-0">
                <label className="text-sm font-semibold block">
                  {field.field_name} {field.is_required && <span className="text-rose-500">*</span>}
                </label>
                
                {field.field_type === "select" ? (
                  <select
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    value={answers[field.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [field.id]: e.target.value })}
                  >
                    <option value="">Select option...</option>
                    {field.options.map((opt: any) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                ) : (
                  <Input
                    value={answers[field.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [field.id]: e.target.value })}
                    placeholder={field.is_required ? "Required answer" : "Optional answer"}
                  />
                )}
              </div>
            ))}
            {fieldList && fieldList.filter(f => !f.resolved || !f.value).length === 0 && (
              <p className="text-sm text-muted-foreground text-center">All fields successfully resolved!</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsResolverOpen(false)}>Cancel</Button>
            <Button onClick={handleResolveSubmit} disabled={resolveMutation.isPending}>
              {resolveMutation.isPending ? (
                <>
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                "Save & Submit Application"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
