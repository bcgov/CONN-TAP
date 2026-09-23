-- Shared hardware-detail helpers, used by checks/02 and checks/13.
-- Applied first by run_validations.py, before any check that calls them.
--
-- Telus writes the variable part of a hardware charge into the label itself -- the
-- financed amount, the term, the expiry date, the covered date range -- so the same
-- charge arrives under many spellings:
--
--   'Easy Payment $27.50 - 2yrs (exp. Mar 2027)'
--   'Easy Payment $40.00 - 3 yrs (exp. Jan 2028)'
--   'Device Care Complete (Mar 15 to Apr 14)'
--
-- Matching those literally would need a new allowlist entry every month. Instead we
-- reduce each description to its word signature and match on that, so one entry
-- covers every amount, term and date.

-- The signature is reference_data.telus_detail_signature (alembic, see
-- app/backend/alembic/reference_data/functions.sql), so these scripts and the dbt
-- models normalize identically: anything in parentheses is dropped, then every
-- character that is not a letter, leaving single-spaced words. It returns '' for
-- NULL, never NULL, so no NULL handling is needed below.

-- TRUE when a detail_description is a Telus cellular hardware charge, whatever the
-- service id or statement category. Note this is only half the rule: the callers still
-- require the row to be wireless-sourced or source_id 164 before trusting it as
-- cellular hardware. See scripts/sql/telus_classification.md for the confirmations.
CREATE OR REPLACE FUNCTION raw_data.fn_telus_is_hardware_detail(p_detail text)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT reference_data.telus_detail_signature(p_detail) = ANY (ARRAY[
    'hardware purchase charge',
    'device discount repayment',
    'monthly telus easy payment',
    'device discount repay canc',      -- 'Device discount repay. canc.'
    'device discount repay cr',        -- 'Device discount repay. - CR'
    'monthly easy payment',
    'telus easy payment balance',
    'equipment adjustment',
    -- Confirmed as cellular hardware by Telus in the March 2026 report validation.
    'gobc mos easy payment fee',       -- 'GoBC 36 Mos Easy Payment Fee (exp. XXX)'
    'gobc data device pom',            -- 'GoBC Data Device PoM'
    'office phone device down payment',-- 'Office Phone - device down payment'
    'smb hardware purchase',           -- 'SMB Hardware Purchase'
    'easy payment yrs',                -- 'Easy Payment $XX.XX - Xyrs (exp. XXX)'
    'device care complete'             -- 'Device Care Complete' / 'Device Care Complete (XX to XX)'
  ]::text[]);
$$;
