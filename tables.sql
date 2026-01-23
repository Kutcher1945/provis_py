CREATE TABLE provisions_source_files (
    id              SERIAL PRIMARY KEY,
    file_name       TEXT NOT NULL,
    file_hash       TEXT UNIQUE,      -- SHA256, чтобы не обрабатывать повторно
    page_count      INTEGER,
    language_hint   TEXT,              -- если знаешь заранее: kaz / rus / mixed
    processed_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT now()
);

CREATE TABLE provisions_document_sections (
    id              SERIAL PRIMARY KEY,
    source_file_id  INTEGER NOT NULL REFERENCES provisions_source_files(id) ON DELETE CASCADE,

    language        TEXT CHECK (language IN ('kaz', 'rus')),
    main_section    TEXT,              -- "3. Основные функции отдела"
    subsection      TEXT,              -- "3.7."
    content         TEXT,

    page_number     INTEGER,           -- опционально, но очень полезно
    created_at      TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_sections_language ON provisions_document_sections(language);
CREATE INDEX idx_sections_main ON provisions_document_sections(main_section);
CREATE INDEX idx_sections_subsection ON provisions_document_sections(subsection);


ALTER TABLE provisions_document_sections
ADD COLUMN content_tsv tsvector;

UPDATE provisions_document_sections
SET content_tsv = to_tsvector('russian', content);

CREATE INDEX idx_sections_fts
ON provisions_document_sections USING GIN(content_tsv);