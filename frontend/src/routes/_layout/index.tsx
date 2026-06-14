import { createFileRoute, Link } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import useAuth from "@/hooks/useAuth"
import { ProfileService, ApplicationsService, JobsService } from "@/client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Briefcase, FileText, HelpCircle, CheckCircle, ArrowRight, UserCheck } from "lucide-react"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - Job Applier",
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  // Load profile completeness
  const { data: profile } = useQuery({
    queryKey: ["profile"],
    queryFn: () => ProfileService.getMyProfile().catch(() => null),
  })

  // Load applications
  const { data: apps } = useQuery({
    queryKey: ["applications"],
    queryFn: () => ApplicationsService.listApplications(),
  })

  // Load matches
  const { data: matches } = useQuery({
    queryKey: ["matchedJobs"],
    queryFn: () => JobsService.getMatchedJobs(),
  })

  // Calculate profile completeness
  const getProfileCompleteness = () => {
    if (!profile) return 0
    let points = 0
    let total = 6

    if (profile.personal_info && Object.keys(profile.personal_info).length > 0) points++
    if (profile.skills && profile.skills.length > 0) points++
    if (profile.education && profile.education.length > 0) points++
    if (profile.experience && profile.experience.length > 0) points++
    if (profile.portfolio_links && profile.portfolio_links.length > 0) points++
    if (profile.preferences && Object.keys(profile.preferences).length > 0) points++

    return Math.round((points / total) * 100)
  }

  const completeness = getProfileCompleteness()
  const totalApps = apps?.length || 0
  const actionApps = apps?.filter(a => a.status === "WAITING_FOR_USER").length || 0
  const submittedApps = apps?.filter(a => a.status === "SUBMITTED").length || 0

  return (
    <div className="flex flex-col gap-8 pb-12">
      {/* Welcome Banner */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">
            Hi, {currentUser?.full_name || currentUser?.email} 👋
          </h1>
          <p className="text-muted-foreground mt-1">
            Welcome back to your job automation control center.
          </p>
        </div>
      </div>

      {/* Stats Summary Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* Profile Completeness */}
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Profile Score</CardTitle>
            <UserCheck className="h-4.5 w-4.5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completeness}%</div>
            <div className="w-full bg-secondary h-2.5 rounded-full mt-3 overflow-hidden">
              <div
                className="bg-primary h-full rounded-full transition-all duration-500"
                style={{ width: `${completeness}%` }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Total Applications */}
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
            <Briefcase className="h-4.5 w-4.5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalApps}</div>
            <p className="text-xs text-muted-foreground mt-1">In progress or submitted</p>
          </CardContent>
        </Card>

        {/* Action Required */}
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Actions Required</CardTitle>
            <HelpCircle className="h-4.5 w-4.5 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">{actionApps}</div>
            <p className="text-xs text-muted-foreground mt-1">Pauses needing details</p>
          </CardContent>
        </Card>

        {/* Submitted */}
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Submitted Applications</CardTitle>
            <CheckCircle className="h-4.5 w-4.5 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{submittedApps}</div>
            <p className="text-xs text-muted-foreground mt-1">Completed successfully</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Left column: Action items & Matches */}
        <div className="lg:col-span-2 space-y-8">
          {/* Matches Preview */}
          <Card className="shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Top Job Matches</CardTitle>
                <CardDescription>Based on your parsed resume and skills list.</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/jobs">
                  View All <ArrowRight className="ml-1.5 h-4 w-4" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {matches && matches.length > 0 ? (
                matches.slice(0, 3).map((match) => (
                  <div key={match.job.id} className="flex justify-between items-center border-b pb-4 last:border-0 last:pb-0">
                    <div>
                      <h4 className="font-semibold text-sm">{match.job.title}</h4>
                      <p className="text-xs text-muted-foreground mt-0.5">{match.job.company} — {match.job.location}</p>
                    </div>
                    <Badge variant="outline" className="font-semibold bg-green-500/10 text-green-500 border-green-500/20">
                      {Math.round(match.score * 100)}% Match
                    </Badge>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-6">No matches calculated yet. Upload a resume to start.</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column: Quick links / profile overview */}
        <div className="space-y-8">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Resume Parser</CardTitle>
              <CardDescription>Quickly parse new resumes to overwrite your profile details.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 bg-muted p-4 rounded-lg">
                <FileText className="h-8 w-8 text-primary shrink-0" />
                <div>
                  <p className="font-semibold text-sm">Resume parsing active</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Quickly import details.</p>
                </div>
              </div>
              <Button className="w-full" asChild>
                <Link to="/resume">Go to Resumes</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
export default Dashboard
