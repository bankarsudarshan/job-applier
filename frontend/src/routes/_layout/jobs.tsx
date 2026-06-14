import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { JobsService, ApplicationsService } from "@/client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import { Loader2, Briefcase, MapPin, Compass, Sparkles, Send } from "lucide-react"

export const Route = createFileRoute("/_layout/jobs")({
  component: JobsPage,
  head: () => ({
    meta: [
      {
        title: "Jobs - Job Applier",
      },
    ],
  }),
})

function JobsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  // Load recommended matches
  const { data: matchedJobs, isLoading } = useQuery({
    queryKey: ["matchedJobs"],
    queryFn: () => JobsService.getMatchedJobs(),
  })

  // Discover jobs mutation
  const discoverMutation = useMutation({
    mutationFn: () => JobsService.discoverNewJobs(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["matchedJobs"] })
      toast.success("Discovered new jobs successfully!")
    },
    onError: () => {
      toast.error("Failed to run job discovery.")
    }
  })

  // Create & Start application
  const applyMutation = useMutation({
    mutationFn: async (jobId: string) => {
      const app = await ApplicationsService.createApplication({
        requestBody: { job_id: jobId }
      })
      await ApplicationsService.startApplying({ appId: app.id })
      return app
    },
    onSuccess: () => {
      toast.success("Application runner started successfully!")
      navigate({ to: "/applications" })
    },
    onError: () => {
      toast.error("Failed to start application process.")
    }
  })

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "bg-green-500/10 text-green-500 border-green-500/20"
    if (score >= 0.5) return "bg-amber-500/10 text-amber-500 border-amber-500/20"
    return "bg-rose-500/10 text-rose-500 border-rose-500/20"
  };

  return (
    <div className="flex flex-col gap-8 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Job Recommendations</h1>
          <p className="text-muted-foreground">Semantic matching maps your skills & experience to discover best-fit job postings.</p>
        </div>
        <Button onClick={() => discoverMutation.mutate()} disabled={discoverMutation.isPending}>
          {discoverMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Compass className="mr-2 h-4 w-4" />
          )}
          Crawl / Discover Jobs
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-24">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </div>
      ) : matchedJobs && matchedJobs.length > 0 ? (
        <div className="grid grid-cols-1 gap-6">
          {matchedJobs.map((match) => (
            <Card key={match.job.id} className="shadow-sm hover:shadow-md transition-shadow relative overflow-hidden border">
              {/* Score indicator badge */}
              <div className="absolute right-6 top-6 flex items-center gap-2">
                <Badge variant="outline" className={`py-1.5 px-3 font-semibold ${getScoreColor(match.score)}`}>
                  <Sparkles className="h-3.5 w-3.5 mr-1" />
                  {Math.round(match.score * 100)}% Match
                </Badge>
              </div>

              <CardHeader className="pr-36">
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <Briefcase className="h-5 w-5 text-primary shrink-0" />
                  {match.job.title}
                </CardTitle>
                <CardDescription className="text-base font-semibold mt-1">
                  {match.job.company}
                </CardDescription>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-2">
                  <MapPin className="h-3.5 w-3.5" />
                  <span>{match.job.location}</span>
                  {match.job.ats_type && (
                    <>
                      <span className="mx-1">•</span>
                      <span className="bg-muted px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider">{match.job.ats_type} ATS</span>
                    </>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground line-clamp-3">
                  {match.job.description}
                </p>

                <div className="flex justify-end gap-2 pt-2 border-t">
                  <Button
                    onClick={() => applyMutation.mutate(match.job.id)}
                    disabled={applyMutation.isPending}
                    size="sm"
                  >
                    {applyMutation.isPending ? (
                      <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="mr-1.5 h-4 w-4" />
                    )}
                    Apply Automatically
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-24 text-muted-foreground border-2 border-dashed rounded-lg">
          <Briefcase className="h-16 w-16 mx-auto mb-4 opacity-20" />
          <h3 className="text-lg font-bold">No jobs found</h3>
          <p className="text-sm mt-1">Click the Crawl / Discover button to fetch jobs.</p>
        </div>
      )}
    </div>
  )
}
