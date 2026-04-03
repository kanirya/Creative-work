-- Migration: Fix announcement priority enum values to match C# enum
-- Changes lowercase values to PascalCase to match AnnouncementPriority enum

-- Drop the old constraint first
ALTER TABLE announcements DROP CONSTRAINT IF EXISTS chk_announcement_priority;

-- Update existing data (if any)
UPDATE announcements SET priority = 'Low' WHERE priority = 'low';
UPDATE announcements SET priority = 'Normal' WHERE priority = 'normal';
UPDATE announcements SET priority = 'High' WHERE priority = 'high';
UPDATE announcements SET priority = 'Urgent' WHERE priority = 'urgent';

-- Add new constraint with PascalCase values
ALTER TABLE announcements ADD CONSTRAINT chk_announcement_priority 
    CHECK (priority IN ('Low', 'Normal', 'High', 'Urgent'));

-- Update the default value
ALTER TABLE announcements ALTER COLUMN priority SET DEFAULT 'Normal';
