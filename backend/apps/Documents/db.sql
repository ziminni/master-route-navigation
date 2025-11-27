-- ============================================
-- CISC V-Hub: Document Vault & Form Repository
-- Updated Database Schema - PostgreSQL
-- With Improved Access Control & Approval Workflow
-- ============================================

-- ========================================
-- PHASE 1: CORE TABLES
-- ========================================

-- Table: categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_display_order ON categories(display_order);
CREATE INDEX idx_categories_slug ON categories(slug);

-- Table: documents
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    file_extension VARCHAR(10),
    mime_type VARCHAR(100),
    
    -- Foreign Keys
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE PROTECT,
    uploaded_by_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL,
    
    -- Timestamps
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    view_count INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_documents_category_uploaded ON documents(category_id, uploaded_at DESC);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by_id);
CREATE INDEX idx_documents_organization ON documents(organization_id);
CREATE INDEX idx_documents_is_active ON documents(is_active);
CREATE INDEX idx_documents_is_featured ON documents(is_featured) WHERE is_featured = TRUE;

COMMENT ON COLUMN documents.organization_id IS 'NULL = college-wide document, NOT NULL = organization-specific document';
COMMENT ON COLUMN documents.view_count IS 'Quick access counter, incremented on each view';
COMMENT ON COLUMN documents.is_featured IS 'Highlight important/featured documents on homepage';


-- ========================================
-- PHASE 2: ACCESS CONTROL & DOCUMENT TYPES
-- ========================================

-- Table: document_types
CREATE TABLE document_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    allowed_extensions TEXT,
    max_file_size_mb INTEGER DEFAULT 10,
    requires_approval BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_types_slug ON document_types(slug);

COMMENT ON COLUMN document_types.allowed_extensions IS 'JSON array stored as text: ["pdf","docx","xlsx"]';
COMMENT ON COLUMN document_types.requires_approval IS 'If TRUE, uploads auto-create approval record';

-- Add document_type_id to documents
ALTER TABLE documents 
    ADD COLUMN document_type_id INTEGER REFERENCES document_types(id) ON DELETE PROTECT;

CREATE INDEX idx_documents_document_type ON documents(document_type_id);

-- Table: document_permissions (IMPROVED ACCESS CONTROL)
CREATE TABLE document_permissions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    can_view BOOLEAN DEFAULT TRUE,
    can_download BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_permissions_document ON document_permissions(document_id);
CREATE INDEX idx_document_permissions_role ON document_permissions(role);
CREATE UNIQUE INDEX idx_document_permissions_unique ON document_permissions(document_id, role);

COMMENT ON TABLE document_permissions IS 'Flexible access control - multiple roles per document';
COMMENT ON COLUMN document_permissions.role IS 'Values: public, students, faculty, org_officers, admin, or specific org slugs';

-- Add constraint for valid roles (can be extended later)
ALTER TABLE document_permissions 
    ADD CONSTRAINT chk_permission_role 
    CHECK (role ~ '^[a-z0-9_-]+$');


-- ========================================
-- PHASE 3: TAGGING SYSTEM
-- ========================================

-- Table: tags
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#3B82F6',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tags_slug ON tags(slug);

COMMENT ON COLUMN tags.color IS 'Hex color code for UI badges (e.g., #EF4444 for red)';

-- Table: document_tags (Junction Table)
CREATE TABLE document_tags (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_document_tag UNIQUE (document_id, tag_id)
);

CREATE INDEX idx_document_tags_document ON document_tags(document_id);
CREATE INDEX idx_document_tags_tag ON document_tags(tag_id);


-- ========================================
-- PHASE 4: IMPROVED APPROVAL WORKFLOW
-- ========================================

-- Table: document_approvals (IMPROVED)
CREATE TABLE document_approvals (
    id SERIAL PRIMARY KEY,
    document_id INTEGER UNIQUE NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending',
    previous_status VARCHAR(20),
    resubmission_count INTEGER DEFAULT 0,
    
    -- Timestamps
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    last_resubmitted_at TIMESTAMP,
    
    -- Reviewer info
    reviewed_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    review_notes TEXT,
    
    -- Uploader notes on resubmission
    resubmission_notes TEXT
);

CREATE INDEX idx_document_approvals_status ON document_approvals(status);
CREATE INDEX idx_document_approvals_document ON document_approvals(document_id);
CREATE INDEX idx_document_approvals_reviewed_by ON document_approvals(reviewed_by_id);

-- Add constraint for valid status values
ALTER TABLE document_approvals 
    ADD CONSTRAINT chk_approval_status 
    CHECK (status IN ('pending', 'approved', 'rejected', 'resubmitted'));

COMMENT ON COLUMN document_approvals.status IS 'pending = awaiting review, approved = published, rejected = needs changes, resubmitted = re-uploaded after rejection';
COMMENT ON COLUMN document_approvals.previous_status IS 'Tracks status history for audit trail';
COMMENT ON COLUMN document_approvals.resubmission_count IS 'Number of times document was resubmitted after rejection';
COMMENT ON COLUMN document_approvals.last_resubmitted_at IS 'Timestamp of most recent resubmission';
COMMENT ON COLUMN document_approvals.resubmission_notes IS 'Uploader explanation of changes made';

-- Table: approval_history (Audit trail for status changes)
CREATE TABLE approval_history (
    id SERIAL PRIMARY KEY,
    approval_id INTEGER NOT NULL REFERENCES document_approvals(id) ON DELETE CASCADE,
    status_from VARCHAR(20),
    status_to VARCHAR(20) NOT NULL,
    changed_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX idx_approval_history_approval ON approval_history(approval_id, changed_at DESC);
CREATE INDEX idx_approval_history_changed_by ON approval_history(changed_by_id);

COMMENT ON TABLE approval_history IS 'Complete audit trail of all approval status changes';


-- ========================================
-- PHASE 5: ANALYTICS & TRACKING
-- ========================================

-- Table: document_downloads
CREATE TABLE document_downloads (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_document_downloads_document_date ON document_downloads(document_id, downloaded_at DESC);
CREATE INDEX idx_document_downloads_user ON document_downloads(user_id);
CREATE INDEX idx_document_downloads_date ON document_downloads(downloaded_at DESC);

COMMENT ON COLUMN document_downloads.user_agent IS 'Browser/app identifier for analytics';


-- ========================================
-- PHASE 6: VERSION CONTROL (ADVANCED)
-- ========================================

-- Table: document_versions
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    uploaded_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_notes TEXT,
    
    CONSTRAINT unique_document_version UNIQUE (document_id, version_number)
);

CREATE INDEX idx_document_versions_document ON document_versions(document_id, version_number DESC);

COMMENT ON TABLE document_versions IS 'Historical versions of documents - main documents table always has latest';


-- ========================================
-- TRIGGERS & FUNCTIONS
-- ========================================

-- Function: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to documents table
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply to categories table
CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply to document_types table
CREATE TRIGGER update_document_types_updated_at
    BEFORE UPDATE ON document_types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- Function: Auto-create approval record when needed
CREATE OR REPLACE FUNCTION create_approval_if_required()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.document_type_id IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM document_types 
            WHERE id = NEW.document_type_id 
            AND requires_approval = TRUE
        ) THEN
            INSERT INTO document_approvals (document_id, status, submitted_at)
            VALUES (NEW.id, 'pending', CURRENT_TIMESTAMP);
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger
CREATE TRIGGER auto_create_approval
    AFTER INSERT ON documents
    FOR EACH ROW
    EXECUTE FUNCTION create_approval_if_required();


-- Function: Log approval status changes to history
CREATE OR REPLACE FUNCTION log_approval_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO approval_history (
            approval_id, 
            status_from, 
            status_to, 
            changed_by_id, 
            notes
        ) VALUES (
            NEW.id,
            OLD.status,
            NEW.status,
            NEW.reviewed_by_id,
            NEW.review_notes
        );
        
        -- Update previous_status
        NEW.previous_status := OLD.status;
        
        -- If status changed to 'resubmitted', increment counter
        IF NEW.status = 'resubmitted' THEN
            NEW.resubmission_count := OLD.resubmission_count + 1;
            NEW.last_resubmitted_at := CURRENT_TIMESTAMP;
        END IF;
        
        -- If status changed to 'approved' or 'rejected', set reviewed_at
        IF NEW.status IN ('approved', 'rejected') AND OLD.reviewed_at IS NULL THEN
            NEW.reviewed_at := CURRENT_TIMESTAMP;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger
CREATE TRIGGER log_approval_changes
    BEFORE UPDATE ON document_approvals
    FOR EACH ROW
    EXECUTE FUNCTION log_approval_status_change();


-- ========================================
-- SAMPLE DATA (OPTIONAL - FOR TESTING)
-- ========================================

-- Sample Categories
INSERT INTO categories (name, slug, description, display_order) VALUES
    ('Syllabi', 'syllabi', 'Course syllabi and curriculum documents', 1),
    ('Forms', 'forms', 'Official forms and templates', 2),
    ('Memos', 'memos', 'Administrative memos and announcements', 3),
    ('Organization Documents', 'org-documents', 'Student organization materials', 4),
    ('Academic Resources', 'academic-resources', 'Study guides and reference materials', 5);

-- Sample Document Types
INSERT INTO document_types (name, slug, description, allowed_extensions, max_file_size_mb, requires_approval) VALUES
    ('Syllabus', 'syllabus', 'Course syllabus document', '["pdf","docx"]', 10, FALSE),
    ('Official Memo', 'memo', 'Administrative memorandum', '["pdf"]', 5, TRUE),
    ('Form Template', 'form', 'Downloadable form template', '["pdf","docx","xlsx"]', 10, FALSE),
    ('Organization Charter', 'org-charter', 'Student organization charter', '["pdf","docx"]', 10, TRUE),
    ('Administrative Document', 'admin-doc', 'Internal administrative document', '["pdf","docx"]', 20, TRUE);

-- Sample Tags
INSERT INTO tags (name, slug, color) VALUES
    ('Urgent', 'urgent', '#EF4444'),
    ('IT Department', 'it-dept', '#3B82F6'),
    ('CS Department', 'cs-dept', '#8B5CF6'),
    ('First Year', '1st-year', '#10B981'),
    ('Scholarship', 'scholarship', '#F59E0B'),
    ('Required Reading', 'required', '#EC4899'),
    ('Optional', 'optional', '#6B7280');


-- ========================================
-- USEFUL QUERIES (DOCUMENTATION)
-- ========================================

-- Check if user has permission to view document
COMMENT ON TABLE document_permissions IS 
'Query example: 
SELECT d.* FROM documents d
JOIN document_permissions dp ON d.id = dp.document_id
WHERE dp.role IN (''students'', ''public'') 
AND dp.can_view = TRUE;';

-- Get all pending approvals
COMMENT ON COLUMN document_approvals.status IS
'Query example for pending approvals:
SELECT d.title, da.submitted_at, u.username as uploader
FROM document_approvals da
JOIN documents d ON da.document_id = d.id
JOIN auth_user u ON d.uploaded_by_id = u.id
WHERE da.status = ''pending''
ORDER BY da.submitted_at ASC;';

-- Get document with approval history
COMMENT ON TABLE approval_history IS
'Query example for full approval timeline:
SELECT 
    d.title,
    ah.status_from,
    ah.status_to,
    ah.changed_at,
    u.username as changed_by,
    ah.notes
FROM approval_history ah
JOIN document_approvals da ON ah.approval_id = da.id
JOIN documents d ON da.document_id = d.id
LEFT JOIN auth_user u ON ah.changed_by_id = u.id
WHERE d.id = 123
ORDER BY ah.changed_at DESC;';