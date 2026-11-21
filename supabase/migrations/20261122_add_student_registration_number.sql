-- Give each student a unique registration number, starting at 2307060023.
-- The first ten assigned numbers are 2307060023 through 2307060032.

ALTER TABLE public.students
ADD COLUMN IF NOT EXISTS registration_number text;

CREATE SEQUENCE IF NOT EXISTS public.student_registration_number_seq
    AS bigint
    START WITH 2307060023
    INCREMENT BY 1;

-- Backfill existing student rows in student_id order.
UPDATE public.students
SET registration_number = nextval('public.student_registration_number_seq')::text
WHERE registration_number IS NULL OR btrim(registration_number) = '';

-- Continue after any existing numeric registration number on repeat runs.
SELECT setval(
    'public.student_registration_number_seq',
    GREATEST(
        2307060023,
        COALESCE(
            (SELECT MAX(registration_number::bigint) + 1
             FROM public.students
             WHERE registration_number ~ '^[0-9]+$'),
            2307060023
        )
    ),
    false
);

CREATE OR REPLACE FUNCTION public.assign_student_registration_number()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.registration_number IS NULL OR btrim(NEW.registration_number) = '' THEN
        NEW.registration_number := nextval(
            'public.student_registration_number_seq'
        )::text;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_student_registration_number ON public.students;
CREATE TRIGGER set_student_registration_number
BEFORE INSERT ON public.students
FOR EACH ROW
EXECUTE FUNCTION public.assign_student_registration_number();

CREATE UNIQUE INDEX IF NOT EXISTS students_registration_number_unique
ON public.students (registration_number)
WHERE registration_number IS NOT NULL;
