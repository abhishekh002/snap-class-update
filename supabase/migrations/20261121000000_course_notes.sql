create table if not exists public.course_notes (
    id text primary key,
    subject_id text not null,
    subject_name text not null,
    teacher_id text not null,
    teacher_name text not null,
    title text not null,
    description text not null default '',
    file_name text,
    file_path text,
    file_size_kb numeric not null default 0,
    created_at text not null
);

create index if not exists course_notes_teacher_created_idx
    on public.course_notes (teacher_id, created_at desc);

create index if not exists course_notes_subject_created_idx
    on public.course_notes (subject_id, created_at desc);

alter table public.course_notes enable row level security;
grant all on table public.course_notes to service_role;

insert into storage.buckets (id, name, public)
values ('course-note-files', 'course-note-files', false)
on conflict (id) do update set public = false;
