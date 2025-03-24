import { Tables } from "./db";

type Upload = Tables<"uploads">;
type Course = Tables<"courses">;
type Professor = Tables<"professors">;
export type Tags = Tables<"tags">;

export type UploadWithRelations = Upload & {
    courses: Course;
    professors: Professor;
};

export type UserUploadedFile = {
    id: number;
    semester: string;
    year: number;
    fileurl: string;
    courses: {
        id: number;
        course_number: number;
        course_subject: string;
        name: string;
    };
    professors: {
        name: string;
        firebase_id: string | null;
    };
};