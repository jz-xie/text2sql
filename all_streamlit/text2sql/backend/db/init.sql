-- create login session
CREATE TABLE IF NOT EXISTS login_session (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    login_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- create chat history
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    question VARCHAR,
    generated_sql VARCHAR,
    state VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- create chat history
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL,
    feedback VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);