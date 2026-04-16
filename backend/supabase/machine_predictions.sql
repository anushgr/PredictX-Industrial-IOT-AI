-- Machine predictions table for DL model outputs and failure risk scores
-- Stores predicted failures, anomaly flags, and recommended actions per window

CREATE TABLE IF NOT EXISTS machine_predictions (
    id BIGSERIAL PRIMARY KEY,
    machine_id TEXT NOT NULL,
    sensor TEXT NOT NULL,
    prediction_score FLOAT NOT NULL,
    anomaly_flag BOOLEAN NOT NULL DEFAULT false,
    failure_probability_percent INT,
    recommended_action TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_machine_predictions_machine_id ON machine_predictions(machine_id);
CREATE INDEX IF NOT EXISTS idx_machine_predictions_created_at ON machine_predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_machine_predictions_sensor ON machine_predictions(sensor);

-- Row-level security
ALTER TABLE machine_predictions ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'machine_predictions' AND policyname = 'allow_public_read'
    ) THEN
        CREATE POLICY "allow_public_read" ON machine_predictions
            FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'machine_predictions' AND policyname = 'allow_service_write'
    ) THEN
        CREATE POLICY "allow_service_write" ON machine_predictions
            FOR INSERT WITH CHECK (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE tablename = 'machine_predictions' AND policyname = 'allow_service_update'
    ) THEN
        CREATE POLICY "allow_service_update" ON machine_predictions
            FOR UPDATE USING (true);
    END IF;
END
$$;
