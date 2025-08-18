-- Initialize A3E Database with all US accreditation data
-- This script seeds the database with accrediting bodies and their standards

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Insert Regional Accreditors
INSERT INTO accreditors (id, name, acronym, type, recognition_authority, geographic_scope, applicable_institution_types, website, is_active) VALUES
('neche', 'New England Commission of Higher Education', 'NECHE', 'regional', 'USDE', '["CT", "ME", "MA", "NH", "RI", "VT"]', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', 'https://www.neche.org', true),
('msche', 'Middle States Commission on Higher Education', 'MSCHE', 'regional', 'USDE', '["DE", "MD", "NJ", "NY", "PA", "DC", "PR", "VI"]', '["community_college", "four_year_college", "university", "research_university", "graduate_school", "professional_school"]', 'https://www.msche.org', true),
('sacscoc', 'Southern Association of Colleges and Schools Commission on Colleges', 'SACSCOC', 'regional', 'USDE', '["AL", "FL", "GA", "KY", "LA", "MS", "NC", "SC", "TN", "TX", "VA"]', '["community_college", "four_year_college", "university", "research_university", "graduate_school", "professional_school"]', 'https://www.sacscoc.org', true),
('hlc', 'Higher Learning Commission', 'HLC', 'regional', 'USDE', '["AZ", "AR", "CO", "IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "NM", "ND", "OH", "OK", "SD", "WV", "WI", "WY"]', '["community_college", "four_year_college", "university", "research_university", "graduate_school", "professional_school"]', 'https://www.hlcommission.org', true),
('nwccu', 'Northwest Commission on Colleges and Universities', 'NWCCU', 'regional', 'USDE', '["AK", "ID", "MT", "NV", "OR", "UT", "WA"]', '["community_college", "four_year_college", "university", "research_university", "graduate_school", "professional_school"]', 'https://www.nwccu.org', true),
('wscuc', 'WASC Senior College and University Commission', 'WSCUC', 'regional', 'USDE', '["CA", "HI", "Territory of Guam", "Commonwealth of the Northern Mariana Islands"]', '["four_year_college", "university", "research_university", "graduate_school"]', 'https://www.wscuc.org', true),
('accjc', 'Accrediting Commission for Community and Junior Colleges', 'ACCJC', 'regional', 'USDE', '["CA", "HI", "Territory of Guam", "Commonwealth of the Northern Mariana Islands", "Republic of Palau", "Federated States of Micronesia", "Republic of the Marshall Islands", "American Samoa"]', '["community_college"]', 'https://www.accjc.org', true);

-- Insert Major National Accreditors
INSERT INTO accreditors (id, name, acronym, type, recognition_authority, geographic_scope, applicable_institution_types, website, is_active) VALUES
('abhe', 'Association for Biblical Higher Education', 'ABHE', 'national', 'USDE', '["National"]', '["theological_seminary", "four_year_college", "specialized_institution"]', 'https://www.abhe.org', true),
('deac', 'Distance Education Accrediting Commission', 'DEAC', 'national', 'USDE', '["National", "International"]', '["online_institution", "specialized_institution", "for_profit"]', 'https://www.deac.org', true),
('tracs', 'Transnational Association of Christian Colleges and Schools', 'TRACS', 'national', 'USDE', '["National"]', '["four_year_college", "university", "theological_seminary", "specialized_institution"]', 'https://www.tracs.org', true);

-- Insert Major Programmatic Accreditors
INSERT INTO accreditors (id, name, acronym, type, recognition_authority, geographic_scope, applicable_institution_types, website, is_active) VALUES
('aacsb', 'Association to Advance Collegiate Schools of Business', 'AACSB', 'programmatic', 'CHEA', '["National", "International"]', '["university", "four_year_college", "graduate_school"]', 'https://www.aacsb.edu', true),
('abet', 'ABET (Accreditation Board for Engineering and Technology)', 'ABET', 'programmatic', 'CHEA', '["National", "International"]', '["university", "four_year_college", "community_college"]', 'https://www.abet.org', true),
('acbsp', 'Accreditation Council for Business Schools and Programs', 'ACBSP', 'programmatic', 'CHEA', '["National", "International"]', '["community_college", "four_year_college", "university"]', 'https://www.acbsp.org', true),
('acen', 'Accreditation Commission for Education in Nursing', 'ACEN', 'programmatic', 'USDE', '["National"]', '["community_college", "four_year_college", "university", "graduate_school"]', 'https://www.acenursing.org', true),
('ccne', 'Commission on Collegiate Nursing Education', 'CCNE', 'programmatic', 'USDE', '["National"]', '["four_year_college", "university", "graduate_school"]', 'https://www.aacnnursing.org/ccne', true);

-- Insert sample MSCHE standards (most common regional accreditor)
INSERT INTO standards (id, accreditor_id, title, description, applicable_institution_types, evidence_requirements, weight, order_sequence, level) VALUES
('msche_1', 'msche', 'Mission and Goals', 'The institution''s mission defines its purpose within the context of higher education and indicates who the institution serves and what it intends to accomplish.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["mission_statement", "strategic_plan", "board_minutes", "institutional_publications", "website_content"]', 1.0, 1, 1),
('msche_2', 'msche', 'Ethics and Integrity', 'Ethics and integrity are central, indispensable, and defining hallmarks of effective higher education institutions.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["code_of_ethics", "conflict_of_interest_policies", "academic_integrity_policies", "financial_transparency", "compliance_reports"]', 1.0, 2, 1),
('msche_3', 'msche', 'Design and Delivery of the Student Learning Experience', 'The institution provides students with learning experiences that are characterized by rigor and coherence at all program, certificate, and degree levels.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["curriculum_documents", "program_reviews", "learning_outcomes", "assessment_data", "syllabi", "faculty_qualifications"]', 1.0, 3, 1),
('msche_4', 'msche', 'Support of the Student Experience', 'Across all educational experiences, settings, levels, and instructional modalities, the institution recruits and admits students whose interests, abilities, experiences, and goals are congruent with its mission and educational offerings.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["admissions_data", "student_services_documentation", "retention_rates", "graduation_rates", "student_support_programs"]', 1.0, 4, 1),
('msche_5', 'msche', 'Educational Effectiveness Assessment', 'Assessment of student learning and achievement demonstrates that the institution''s students have accomplished educational goals consistent with their program of study, degree level, the institution''s mission, and appropriate expectations.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["assessment_plans", "assessment_reports", "learning_outcomes_data", "program_evaluation", "institutional_research"]', 1.0, 5, 1),
('msche_6', 'msche', 'Planning, Resources, and Institutional Improvement', 'The institution''s planning processes, resources, and structures are aligned with each other and are sufficient to fulfill its mission and goals.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["strategic_plans", "budget_documents", "financial_audits", "facilities_plans", "technology_plans", "institutional_research"]', 1.0, 6, 1),
('msche_7', 'msche', 'Governance, Leadership, and Administration', 'The institution is governed and administered in a manner that allows it to realize its stated mission and goals in a way that effectively benefits the institution, its students, and the other constituencies it serves.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["organizational_charts", "board_bylaws", "governance_policies", "administrative_procedures", "leadership_qualifications"]', 1.0, 7, 1),
('msche_8', 'msche', 'Faculty', 'The institution''s faculty are appropriately qualified and sufficient in number to deliver the curriculum and reach other goals of the institution.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["faculty_credentials", "faculty_handbook", "hiring_procedures", "professional_development", "faculty_evaluation", "workload_documentation"]', 1.0, 8, 1);

-- Insert sample HLC criteria (second most common)
INSERT INTO standards (id, accreditor_id, title, description, applicable_institution_types, evidence_requirements, weight, order_sequence, level) VALUES
('hlc_1', 'hlc', 'Mission', 'The institution''s mission is clear and articulated publicly; it guides the institution''s operations.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["mission_statement", "public_documentation", "operational_alignment", "stakeholder_communication"]', 1.0, 1, 1),
('hlc_2', 'hlc', 'Integrity: Ethical and Responsible Conduct', 'The institution acts with integrity; its conduct is ethical and responsible.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["ethical_policies", "responsible_conduct", "transparency_measures", "compliance_documentation"]', 1.0, 2, 1),
('hlc_3', 'hlc', 'Teaching and Learning: Quality, Resources, and Support', 'The institution provides high quality education, wherever and however its offerings are delivered.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["curriculum_quality", "learning_resources", "faculty_support", "student_support", "assessment_evidence"]', 1.0, 3, 1),
('hlc_4', 'hlc', 'Teaching and Learning: Evaluation and Improvement', 'The institution demonstrates responsibility for the quality of its educational programs, learning environments, and support services.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["program_evaluation", "continuous_improvement", "quality_assurance", "assessment_data", "improvement_plans"]', 1.0, 4, 1),
('hlc_5', 'hlc', 'Resources, Planning, and Institutional Effectiveness', 'The institution''s resources, structures, and processes are sufficient to fulfill its mission, improve the quality of its educational offerings, and respond to future challenges.', '["community_college", "four_year_college", "university", "research_university", "graduate_school"]', '["resource_allocation", "strategic_planning", "institutional_effectiveness", "financial_sustainability", "infrastructure"]', 1.0, 5, 1);

-- Insert sample AACSB standards (major business programmatic accreditor)
INSERT INTO standards (id, accreditor_id, title, description, applicable_institution_types, evidence_requirements, weight, order_sequence, level) VALUES
('aacsb_1', 'aacsb', 'Mission, Impact, and Innovation', 'The business school demonstrates impact and innovation that is meaningful and sustainable for its stakeholders through teaching, research, and service.', '["university", "four_year_college", "graduate_school"]', '["impact_measurement", "innovation_documentation", "stakeholder_engagement", "teaching_innovation", "research_impact"]', 1.0, 1, 1),
('aacsb_2', 'aacsb', 'Strategic Planning', 'The business school demonstrates strategic thinking and planning for continuous improvement and long-term sustainability.', '["university", "four_year_college", "graduate_school"]', '["strategic_plan", "environmental_scanning", "stakeholder_input", "implementation_tracking", "sustainability_planning"]', 1.0, 2, 1),
('aacsb_3', 'aacsb', 'Financial Strategies and Allocation of Resources', 'The business school manages financial and other resources strategically to ensure high-quality outcomes and sustainability.', '["university", "four_year_college", "graduate_school"]', '["financial_strategies", "resource_allocation", "budget_planning", "sustainability_metrics", "quality_outcomes"]', 1.0, 3, 1),
('aacsb_4', 'aacsb', 'Faculty Sufficiency and Qualifications', 'The business school demonstrates faculty sufficiency and deploys and supports faculty to achieve high-quality outcomes consistent with its mission.', '["university", "four_year_college", "graduate_school"]', '["faculty_sufficiency", "faculty_qualifications", "faculty_deployment", "professional_development", "performance_evaluation"]', 1.0, 4, 1),
('aacsb_5', 'aacsb', 'Curricula Management and Assurance of Learning', 'The business school''s curricula facilitate and promote learning consistent with its mission and expected outcomes.', '["university", "four_year_college", "graduate_school"]', '["curriculum_design", "learning_assurance", "assessment_processes", "continuous_improvement", "learning_outcomes"]', 1.0, 5, 1);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_accreditors_type ON accreditors(type);
CREATE INDEX IF NOT EXISTS idx_accreditors_geographic ON accreditors USING GIN(geographic_scope);
CREATE INDEX IF NOT EXISTS idx_accreditors_institution_types ON accreditors USING GIN(applicable_institution_types);
CREATE INDEX IF NOT EXISTS idx_standards_accreditor ON standards(accreditor_id);
CREATE INDEX IF NOT EXISTS idx_standards_institution_types ON standards USING GIN(applicable_institution_types);
CREATE INDEX IF NOT EXISTS idx_evidence_institution ON evidence(institution_id);
CREATE INDEX IF NOT EXISTS idx_evidence_processing_status ON evidence(processing_status);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(evidence_type);

-- Insert sample institution data for testing
INSERT INTO institutions (id, name, ipeds_id, state, city, institution_types, control, total_enrollment, website, is_active) VALUES
(uuid_generate_v4(), 'Sample Community College', '123456', 'CA', 'Los Angeles', '["community_college", "public"]', 'Public', 15000, 'https://www.samplecc.edu', true),
(uuid_generate_v4(), 'Sample State University', '234567', 'NY', 'Buffalo', '["university", "research_university", "public"]', 'Public', 25000, 'https://www.samplesu.edu', true),
(uuid_generate_v4(), 'Sample Private College', '345678', 'MA', 'Boston', '["four_year_college", "private", "non_profit"]', 'Private non-profit', 3500, 'https://www.samplepc.edu', true);

-- Create audit log trigger
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (event_type, entity_type, entity_id, new_values, timestamp)
        VALUES ('create', TG_TABLE_NAME, NEW.id::text, to_jsonb(NEW), NOW());
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (event_type, entity_type, entity_id, old_values, new_values, timestamp)
        VALUES ('update', TG_TABLE_NAME, NEW.id::text, to_jsonb(OLD), to_jsonb(NEW), NOW());
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (event_type, entity_type, entity_id, old_values, timestamp)
        VALUES ('delete', TG_TABLE_NAME, OLD.id::text, to_jsonb(OLD), NOW());
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to key tables
CREATE TRIGGER audit_institutions AFTER INSERT OR UPDATE OR DELETE ON institutions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_evidence AFTER INSERT OR UPDATE OR DELETE ON evidence
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_agent_workflows AFTER INSERT OR UPDATE OR DELETE ON agent_workflows
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
