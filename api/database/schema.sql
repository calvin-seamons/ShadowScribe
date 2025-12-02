-- ShadowScribe 2.0 Database Schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS shadowscribe 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE shadowscribe;

-- Characters table: stores full character data as JSON
CREATE TABLE IF NOT EXISTS characters (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    race VARCHAR(100),
    character_class VARCHAR(100),
    level INT,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Routing feedback table: stores user queries and routing decisions for fine-tuning
CREATE TABLE IF NOT EXISTS routing_feedback (
    id VARCHAR(36) PRIMARY KEY,
    
    -- Query context
    user_query TEXT NOT NULL,
    character_name VARCHAR(255) NOT NULL,
    campaign_id VARCHAR(255) DEFAULT 'main_campaign',
    
    -- Model predictions (what the classifier chose)
    predicted_tools JSON NOT NULL,
    predicted_entities JSON,
    
    -- Model metadata
    classifier_backend VARCHAR(50) DEFAULT 'local',
    classifier_inference_time_ms FLOAT,
    
    -- User feedback (filled in when user corrects)
    is_correct BOOLEAN,
    corrected_tools JSON,
    feedback_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feedback_at TIMESTAMP NULL,
    
    -- Training data status
    exported_for_training BOOLEAN DEFAULT FALSE,
    exported_at TIMESTAMP NULL,
    
    -- Indexes
    INDEX idx_created (created_at),
    INDEX idx_exported (exported_for_training),
    INDEX idx_is_correct (is_correct),
    INDEX idx_character (character_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
