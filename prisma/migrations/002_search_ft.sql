-- Full-text search support for DocumentText
-- Populate existing rows, create GIN index, and trigger to maintain tsvector

CREATE FUNCTION document_text_tsvector_update() RETURNS trigger AS $$
BEGIN
  NEW."searchVector" := to_tsvector('english', coalesce(NEW."text", ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- Backfill existing
UPDATE "DocumentText" SET "searchVector" = to_tsvector('english', coalesce("text", '')) WHERE "searchVector" IS NULL;

-- Index
CREATE INDEX IF NOT EXISTS document_text_search_idx ON "DocumentText" USING GIN ("searchVector");

-- Trigger
DROP TRIGGER IF EXISTS document_text_tsv_update ON "DocumentText";
CREATE TRIGGER document_text_tsv_update BEFORE INSERT OR UPDATE OF "text" ON "DocumentText"
FOR EACH ROW EXECUTE FUNCTION document_text_tsvector_update();
