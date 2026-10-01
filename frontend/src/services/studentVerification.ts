import api from "@/lib/api";

export type StudentApplicationStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "withdrawn";

export interface StudentApplication {
  id: number;
  applicant_name: string;
  institution_name: string;
  course_or_program: string;
  academic_year: string;
  graduation_year: number;
  institution_email: string | null;
  additional_information: string | null;
  status: StudentApplicationStatus;
  created_at: string;
  admin_reviewed_at: string | null;
  rejection_reason: string | null;
  student_entitlement_expires_at: string | null;
  proof_available: boolean;
  user_id?: number;
  user_email?: string | null;
  enrollment_number?: string;
  proof_original_filename?: string | null;
  proof_content_type?: string;
  proof_size?: number;
  admin_reviewed_by?: number | null;
}

export interface StudentVerificationStatus {
  application: StudentApplication | null;
  student_access_active: boolean;
  effective_plan: string;
  student_access_expires_at: string | null;
}

export interface StudentApplicationList {
  applications: StudentApplication[];
  total: number;
  offset: number;
  limit: number;
}

export interface StudentApplicationInput {
  applicant_name: string;
  institution_name: string;
  enrollment_number: string;
  course_or_program: string;
  academic_year: string;
  graduation_year: string;
  institution_email: string;
  additional_information: string;
  proof_document: File;
}

export async function getMyStudentVerification(): Promise<StudentVerificationStatus> {
  const response = await api.get<StudentVerificationStatus>(
    "/student-verification/me"
  );
  return response.data;
}

export async function submitStudentApplication(
  application: StudentApplicationInput
): Promise<StudentApplication> {
  const formData = new FormData();
  Object.entries(application).forEach(([key, value]) => {
    formData.append(key, value);
  });
  const response = await api.post<StudentApplication>(
    "/student-verification/applications",
    formData
  );
  return response.data;
}

export async function withdrawStudentApplication(
  applicationId: number
): Promise<StudentApplication> {
  const response = await api.post<StudentApplication>(
    `/student-verification/applications/${applicationId}/withdraw`
  );
  return response.data;
}

export async function listStudentApplications(
  statusFilter: string,
  offset: number,
  limit = 25
): Promise<StudentApplicationList> {
  const response = await api.get<StudentApplicationList>(
    "/admin/student-verifications",
    {
      params: {
        ...(statusFilter === "all" ? {} : { status: statusFilter }),
        offset,
        limit,
      },
    }
  );
  return response.data;
}

export async function getStudentApplicationProof(
  applicationId: number
): Promise<Blob> {
  const response = await api.get<Blob>(
    `/admin/student-verifications/${applicationId}/proof`,
    { responseType: "blob" }
  );
  return response.data;
}

export async function approveStudentApplication(
  applicationId: number
): Promise<StudentApplication> {
  const response = await api.post<StudentApplication>(
    `/admin/student-verifications/${applicationId}/approve`
  );
  return response.data;
}

export async function rejectStudentApplication(
  applicationId: number,
  rejectionReason: string
): Promise<StudentApplication> {
  const response = await api.post<StudentApplication>(
    `/admin/student-verifications/${applicationId}/reject`,
    { rejection_reason: rejectionReason }
  );
  return response.data;
}
