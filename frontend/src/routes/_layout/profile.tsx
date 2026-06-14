import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { ProfileService } from "@/client"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { Loader2, Plus, Trash2, Save } from "lucide-react"

export const Route = createFileRoute("/_layout/profile")({
  component: ProfilePage,
  head: () => ({
    meta: [
      {
        title: "Profile - Job Applier",
      },
    ],
  }),
})

function ProfilePage() {
  const queryClient = useQueryClient()
  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => ProfileService.getMyProfile().catch(() => null),
  })

  const updateProfileMutation = useMutation({
    mutationFn: (data: any) => ProfileService.updateMyProfile({ requestBody: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] })
      toast.success("Profile updated successfully!")
    },
    onError: () => {
      toast.error("Failed to update profile.")
    }
  })

  // State management for nested fields
  const [personalInfo, setPersonalInfo] = useState({ first_name: "", last_name: "", email: "", phone: "", address: "" })
  const [preferences, setPreferences] = useState({ target_salary: 0, work_authorization: "", sponsorship_required: "no" })
  const [skills, setSkills] = useState<string[]>([])
  const [newSkill, setNewSkill] = useState("")
  const [portfolioLinks, setPortfolioLinks] = useState<any[]>([])
  const [education, setEducation] = useState<any[]>([])
  const [experience, setExperience] = useState<any[]>([])

  useEffect(() => {
    if (profile) {
      setPersonalInfo((profile.personal_info as any) || { first_name: "", last_name: "", email: "", phone: "", address: "" })
      setPreferences((profile.preferences as any) || { target_salary: 0, work_authorization: "", sponsorship_required: "no" })
      setSkills(profile.skills || [])
      setPortfolioLinks(profile.portfolio_links || [])
      setEducation(profile.education || [])
      setExperience(profile.experience || [])
    }
  }, [profile])

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const handleSave = () => {
    updateProfileMutation.mutate({
      personal_info: personalInfo,
      preferences,
      skills,
      portfolio_links: portfolioLinks,
      education,
      experience
    })
  }

  const addSkill = () => {
    if (newSkill.trim() && !skills.includes(newSkill.trim())) {
      setSkills([...skills, newSkill.trim()])
      setNewSkill("")
    }
  }

  const removeSkill = (skill: string) => {
    setSkills(skills.filter((s) => s !== skill))
  }

  const addLink = () => {
    setPortfolioLinks([...portfolioLinks, { name: "", url: "" }])
  }

  const removeLink = (index: number) => {
    setPortfolioLinks(portfolioLinks.filter((_, i) => i !== index))
  }

  const addEducation = () => {
    setEducation([...education, { institution: "", degree: "", start_date: "", end_date: "" }])
  }

  const removeEducation = (index: number) => {
    setEducation(education.filter((_, i) => i !== index))
  }

  const addExperience = () => {
    setExperience([...experience, { company: "", role: "", description: "", start_date: "", end_date: "" }])
  }

  const removeExperience = (index: number) => {
    setExperience(experience.filter((_, i) => i !== index))
  }

  return (
    <div className="flex flex-col gap-8 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Applicant Profile</h1>
          <p className="text-muted-foreground">Manage your credentials, work history, and application preferences.</p>
        </div>
        <Button onClick={handleSave} size="lg" disabled={updateProfileMutation.isPending}>
          {updateProfileMutation.isPending ? (
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          ) : (
            <Save className="mr-2 h-5 w-5" />
          )}
          Save Changes
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        {/* Personal Info */}
        <Card className="shadow-md">
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
            <CardDescription>Contact info submitted during applications.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-sm font-semibold">First Name</label>
                <Input
                  value={personalInfo.first_name}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, first_name: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-semibold">Last Name</label>
                <Input
                  value={personalInfo.last_name}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, last_name: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-semibold">Email Address</label>
              <Input
                type="email"
                value={personalInfo.email}
                onChange={(e) => setPersonalInfo({ ...personalInfo, email: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-semibold">Phone Number</label>
              <Input
                value={personalInfo.phone}
                onChange={(e) => setPersonalInfo({ ...personalInfo, phone: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-semibold">Home Address</label>
              <Input
                value={personalInfo.address}
                onChange={(e) => setPersonalInfo({ ...personalInfo, address: e.target.value })}
              />
            </div>
          </CardContent>
        </Card>

        {/* Preferences & Skills */}
        <div className="flex flex-col gap-8">
          <Card className="shadow-md">
            <CardHeader>
              <CardTitle>Preferences</CardTitle>
              <CardDescription>Target criteria for job matching.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-semibold">Target Salary ($ / yr)</label>
                <Input
                  type="number"
                  value={preferences.target_salary || ""}
                  onChange={(e) => setPreferences({ ...preferences, target_salary: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-semibold">Work Authorization</label>
                <Input
                  value={preferences.work_authorization}
                  onChange={(e) => setPreferences({ ...preferences, work_authorization: e.target.value })}
                  placeholder="e.g. US Citizen, Permanent Resident"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-semibold">Sponsorship Required?</label>
                <select
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                  value={preferences.sponsorship_required}
                  onChange={(e) => setPreferences({ ...preferences, sponsorship_required: e.target.value })}
                >
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-md">
            <CardHeader>
              <CardTitle>Skills</CardTitle>
              <CardDescription>Core competencies used to match jobs.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  placeholder="e.g. React, Docker, Python"
                  onKeyDown={(e) => e.key === "Enter" && addSkill()}
                />
                <Button onClick={addSkill}>Add</Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {skills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-xs font-semibold text-secondary-foreground"
                  >
                    {skill}
                    <button
                      onClick={() => removeSkill(skill)}
                      className="rounded-full hover:bg-muted p-0.5"
                    >
                      &times;
                    </button>
                  </span>
                ))}
                {skills.length === 0 && (
                  <p className="text-xs text-muted-foreground">No skills added yet.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Portfolio Links */}
      <Card className="shadow-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Portfolio & Social Links</CardTitle>
            <CardDescription>GitHub, LinkedIn, and personal websites.</CardDescription>
          </div>
          <Button onClick={addLink} variant="outline" size="sm">
            <Plus className="mr-1.5 h-4 w-4" /> Add Link
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {portfolioLinks.map((link, idx) => (
            <div key={idx} className="flex gap-4 items-center">
              <Input
                placeholder="Platform / Label (e.g. GitHub)"
                value={link.name}
                onChange={(e) => {
                  const updated = [...portfolioLinks]
                  updated[idx].name = e.target.value
                  setPortfolioLinks(updated)
                }}
                className="flex-1"
              />
              <Input
                placeholder="URL (https://...)"
                value={link.url}
                onChange={(e) => {
                  const updated = [...portfolioLinks]
                  updated[idx].url = e.target.value
                  setPortfolioLinks(updated)
                }}
                className="flex-[2]"
              />
              <Button onClick={() => removeLink(idx)} variant="destructive" size="icon">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          {portfolioLinks.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">No portfolio links added.</p>
          )}
        </CardContent>
      </Card>

      {/* Education */}
      <Card className="shadow-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Education</CardTitle>
            <CardDescription>Degree details and academic credentials.</CardDescription>
          </div>
          <Button onClick={addEducation} variant="outline" size="sm">
            <Plus className="mr-1.5 h-4 w-4" /> Add Education
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {education.map((edu, idx) => (
            <div key={idx} className="border p-4 rounded-lg space-y-4 relative bg-card shadow-sm">
              <Button
                onClick={() => removeEducation(idx)}
                variant="destructive"
                size="icon"
                className="absolute top-4 right-4"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-semibold">School / Institution</label>
                  <Input
                    value={edu.institution}
                    onChange={(e) => {
                      const updated = [...education]
                      updated[idx].institution = e.target.value
                      setEducation(updated)
                    }}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold">Degree / Field of Study</label>
                  <Input
                    value={edu.degree}
                    onChange={(e) => {
                      const updated = [...education]
                      updated[idx].degree = e.target.value
                      setEducation(updated)
                    }}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold">Start Date</label>
                  <Input
                    value={edu.start_date}
                    onChange={(e) => {
                      const updated = [...education]
                      updated[idx].start_date = e.target.value
                      setEducation(updated)
                    }}
                    placeholder="YYYY-MM"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold">End Date (or graduation)</label>
                  <Input
                    value={edu.end_date}
                    onChange={(e) => {
                      const updated = [...education]
                      updated[idx].end_date = e.target.value
                      setEducation(updated)
                    }}
                    placeholder="YYYY-MM"
                  />
                </div>
              </div>
            </div>
          ))}
          {education.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">No education entries added.</p>
          )}
        </CardContent>
      </Card>

      {/* Experience */}
      <Card className="shadow-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Professional Experience</CardTitle>
            <CardDescription>Work history and job roles.</CardDescription>
          </div>
          <Button onClick={addExperience} variant="outline" size="sm">
            <Plus className="mr-1.5 h-4 w-4" /> Add Experience
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {experience.map((exp, idx) => (
            <div key={idx} className="border p-4 rounded-lg space-y-4 relative bg-card shadow-sm">
              <Button
                onClick={() => removeExperience(idx)}
                variant="destructive"
                size="icon"
                className="absolute top-4 right-4"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-semibold">Company Name</label>
                  <Input
                    value={exp.company}
                    onChange={(e) => {
                      const updated = [...experience]
                      updated[idx].company = e.target.value
                      setExperience(updated)
                    }}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold">Role / Job Title</label>
                  <Input
                    value={exp.role}
                    onChange={(e) => {
                      const updated = [...experience]
                      updated[idx].role = e.target.value
                      setExperience(updated)
                    }}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold">Start Date</label>
                  <Input
                    value={exp.start_date}
                    onChange={(e) => {
                      const updated = [...experience]
                      updated[idx].start_date = e.target.value
                      setExperience(updated)
                    }}
                    placeholder="YYYY-MM"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold">End Date (or Present)</label>
                  <Input
                    value={exp.end_date}
                    onChange={(e) => {
                      const updated = [...experience]
                      updated[idx].end_date = e.target.value
                      setExperience(updated)
                    }}
                    placeholder="YYYY-MM"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold">Job Description & Achievements</label>
                <textarea
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                  value={exp.description}
                  onChange={(e) => {
                    const updated = [...experience]
                    updated[idx].description = e.target.value
                    setExperience(updated)
                  }}
                  rows={3}
                />
              </div>
            </div>
          ))}
          {experience.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">No experience entries added.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
