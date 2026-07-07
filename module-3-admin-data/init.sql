-- ===========================================
-- Module 3 Admin Data Database Schema
-- ===========================================

-- profiles table - for message modification (core engine)
CREATE TABLE IF NOT EXISTS profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(100),
    department VARCHAR(100),
    honorific_type VARCHAR(50),
    communication_mode VARCHAR(50),
    known_triggers JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- chat_profiles table - for chat usage (module 2)
CREATE TABLE IF NOT EXISTS chat_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(100),
    department VARCHAR(100),
    honorific_type VARCHAR(50),
    communication_mode VARCHAR(50),
    known_triggers JSONB,
    core_user_id VARCHAR(255), -- reference to profiles.user_id
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (core_user_id) REFERENCES profiles(user_id) ON DELETE SET NULL
);

-- rules table
CREATE TABLE IF NOT EXISTS rules (
    rule_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    role VARCHAR(50),
    priority INTEGER DEFAULT 0,
    condition TEXT,
    action TEXT,
    example_original TEXT,
    example_adapted TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- styles table
CREATE TABLE IF NOT EXISTS styles (
    style_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    tone VARCHAR(50),
    examples JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- documents table
CREATE TABLE IF NOT EXISTS documents (
    document_id VARCHAR(255) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    file_size INTEGER,
    collection VARCHAR(100),
    content TEXT,
    status VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial data from demo_data/profiles.json
INSERT INTO profiles (user_id, full_name, role, department, honorific_type, communication_mode, known_triggers) VALUES
('alex_i', 'Иванов Алексей Петрович', 'engineer', 'backend', 'first_name', 'informal', '["deadline", "bug", "code_review"]'),
('petr_s', 'Смирнов Петр Иванович', 'team_lead', 'backend', 'patronymic', 'formal', '["blame", "deadline"]'),
('anna_k', 'Ковалева Анна Сергеевна', 'director', 'engineering', 'patronymic', 'formal', '["money", "deadline", "blame"]'),
('nonexistent_user_999999', 'Test User 999999', 'employee', 'unknown', 'first_name', 'informal', NULL),
('maria_s', 'Смирнова Мария Дмитриевна', 'hr_manager', 'hr', 'patronymic', 'formal', '["salary", "vacation", "review"]'),
('dmitry_k', 'Кузнецов Дмитрий Александрович', 'senior_engineer', 'backend', 'first_name', 'technical', '["code_review", "deployment", "tech_debt"]'),
('elena_v', 'Воронова Елена Николаевна', 'team_lead', 'frontend', 'patronymic', 'collaborative', '["team_conflict", "deadline", "resources"]'),
('sergey_m', 'Михайлов Сергей Олегович', 'intern', 'marketing', 'first_name', 'informal', '["learning", "feedback", "mentorship"]'),
('olga_a', 'Алексеева Ольга Викторовна', 'director', 'sales', 'title', 'formal', '["revenue", "targets", "clients"]')
ON CONFLICT (user_id) DO NOTHING;

-- Insert initial data from demo_data/rules.json
INSERT INTO rules (rule_id, name, description, category, role, priority, condition, action, is_active) VALUES
('rule_address_formal', 'Формальное обращение', 'Замена ты на вы и добавление отчества для руководства', 'address', 'system', 10, 'recipient_role IN ["team_lead", "director"]', 'replace ''ты'' with ''вы'', add patronymic', true),
('rule_no_blame', 'Без обвинений', 'Переформулировка негативных фраз без обвинений', 'tone', 'system', 9, 'contains ''сломал'' OR ''баг'' OR ''ошибка''', 'rephrase as observation, not blame', true)
ON CONFLICT (rule_id) DO NOTHING;

-- Insert initial data from demo_data/styles.json
INSERT INTO styles (style_id, name, description, category, tone, examples, is_active) VALUES
('chekhov', 'чеховский', 'Стиль Антона Чехова: меланхолия и ирония', 'literary', 'melancholy', '[{"input": "Нужно срочно решить проблему", "output": "Дорогой мой, всё это так грустно... Но, может быть, и добрая улыбка промелькнет на лице судьбы...", "note": "Добавить эмпатию и иронию"}]', true),
('dovlatov', 'довлатовский', 'Стиль Сергея Довлатова: самоирония и советская эпоха', 'literary', 'self-irony', '[{"input": "Ситуация сложная", "output": "В жизни бывает по-разному. Бывает, что человек становится богатым, а бывает, что бедным.", "note": "Добавить самоиронию"}]', true)
ON CONFLICT (style_id) DO NOTHING;

-- Insert initial document from demo_data/corporate_culture.md
INSERT INTO documents (document_id, filename, file_type, file_size, collection, content, status, metadata) VALUES
('doc_corporate_culture', 'corporate_culture.md', 'text/markdown', 8500, 'corporate_rules', '## Корпоративная культура компании "Chameleon"

### Наша миссия
Делать коммуникацию между людьми более эффективной, эмпатичной и продуктивной.

### Наши ценности
1. **Эмпатия** - мы ставим себя на место собеседника
2. **Качество** - каждое сообщение проходит через тщательную адаптацию
3. **Прозрачность** - открытость в коммуникации и принятии решений
4. **Инновации** - постоянный поиск новых решений и улучшений
5. **Командная работа** - мы сильнее вместе', 'processed', '{"author": "Chameleon Team", "version": "1.0"}')
ON CONFLICT (document_id) DO NOTHING;

-- Insert initial chat_profiles (simplified versions of profiles)
INSERT INTO chat_profiles (user_id, full_name, role, department, honorific_type, communication_mode, known_triggers, core_user_id) VALUES
('alex_i', 'Иванов Алексей Петрович', 'engineer', 'backend', 'first_name', 'informal', '["deadline", "bug", "code_review"]', 'alex_i'),
('petr_s', 'Смирнов Петр Иванович', 'team_lead', 'backend', 'patronymic', 'formal', '["blame", "deadline"]', 'petr_s'),
('anna_k', 'Ковалева Анна Сергеевна', 'director', 'engineering', 'patronymic', 'formal', '["money", "deadline", "blame"]', 'anna_k'),
('maria_s', 'Смирнова Мария Дмитриевна', 'hr_manager', 'hr', 'patronymic', 'formal', '["salary", "vacation", "review"]', 'maria_s'),
('dmitry_k', 'Кузнецов Дмитрий Александрович', 'senior_engineer', 'backend', 'first_name', 'technical', '["code_review", "deployment", "tech_debt"]', 'dmitry_k'),
('elena_v', 'Воронова Елена Николаевна', 'team_lead', 'frontend', 'patronymic', 'collaborative', '["team_conflict", "deadline", "resources"]', 'elena_v'),
('sergey_m', 'Михайлов Сергей Олегович', 'intern', 'marketing', 'first_name', 'informal', '["learning", "feedback", "mentorship"]', 'sergey_m'),
('olga_a', 'Алексеева Ольга Викторовна', 'director', 'sales', 'title', 'formal', '["revenue", "targets", "clients"]', 'olga_a')
ON CONFLICT (user_id) DO NOTHING;
