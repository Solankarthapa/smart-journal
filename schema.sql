CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK (
        account_type IN ('debit', 'savings', 'credit_card')
    ),
    institution TEXT,
    current_balance REAL NOT NULL DEFAULT 0,
    credit_limit REAL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    category_id INTEGER,
    transaction_type TEXT NOT NULL CHECK (
        transaction_type IN ('income', 'expense', 'transfer', 'credit_payment')
    ),
    description TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    transaction_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'confirmed', 'posted', 'failed', 'corrected', 'reversed')
    ),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts (id)
        ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories (id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_account_id
    ON transactions(account_id);

CREATE INDEX IF NOT EXISTS idx_transactions_date
    ON transactions(transaction_date);

CREATE INDEX IF NOT EXISTS idx_transactions_status
    ON transactions(status);
