-- create schema
CREATE SCHEMA IF NOT EXISTS csr_reporting AUTHORIZATION postgres;

-- Equity Static
CREATE TABLE IF NOT EXISTS fift.csr_reporting.company_static (
	"symbol" CHAR(12) PRIMARY KEY,
	"security" TEXT,
	"gics_sector"	TEXT,
	"gics_industry"	TEXT,
	"country"	TEXT,
	"region"	TEXT	
);