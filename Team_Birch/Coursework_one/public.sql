/*
 Navicat Premium Data Transfer

 Source Server         : 8.134.166.116
 Source Server Type    : PostgreSQL
 Source Server Version : 100005
 Source Host           : 8.134.166.116:5432
 Source Catalog        : file_storage
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 100005
 File Encoding         : 65001

 Date: 27/02/2025 15:17:35
*/


-- ----------------------------
-- Sequence structure for file_report_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."file_report_id_seq";
CREATE SEQUENCE "public"."file_report_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for users_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."users_id_seq";
CREATE SEQUENCE "public"."users_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 2147483647
START 1
CACHE 1;

-- ----------------------------
-- Table structure for file_report
-- ----------------------------
DROP TABLE IF EXISTS "public"."file_report";
CREATE TABLE "public"."file_report" (
  "id" "pg_catalog"."int4" NOT NULL DEFAULT nextval('file_report_id_seq'::regclass),
  "company_name" "pg_catalog"."varchar" COLLATE "pg_catalog"."default" NOT NULL,
  "report_date" "pg_catalog"."int4" NOT NULL,
  "file_name" "pg_catalog"."varchar" COLLATE "pg_catalog"."default" NOT NULL,
  "file_url" "pg_catalog"."varchar" COLLATE "pg_catalog"."default" NOT NULL
)
;

-- ----------------------------
-- Records of file_report
-- ----------------------------
INSERT INTO "public"."file_report" VALUES (1, 'Adobe', 2022, 'Adobe_2022_CSR.pdf', 'http://8.134.166.116:9000/pdf-reports/Adobe_2022_report.pdf');
INSERT INTO "public"."file_report" VALUES (2, 'Tesla', 2019, 'Tesla_2019_CSR.pdf', 'http://8.134.166.116:9000/pdf-reports/Tesla_2019_report.pdf');
INSERT INTO "public"."file_report" VALUES (3, 'Adobe', 2022, 'Adobe_2022_CSR.pdf', 'http://8.134.166.116:9000/pdf-reports/Adobe_2022_ee19ba791fdb4ee88b498a38917daa4d_report.pdf');

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS "public"."users";
CREATE TABLE "public"."users" (
  "id" "pg_catalog"."int4" NOT NULL DEFAULT nextval('users_id_seq'::regclass),
  "username" "pg_catalog"."varchar" COLLATE "pg_catalog"."default" NOT NULL,
  "password" "pg_catalog"."varchar" COLLATE "pg_catalog"."default" NOT NULL
)
;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO "public"."users" VALUES (1, 'ademos', '123');

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."file_report_id_seq"
OWNED BY "public"."file_report"."id";
SELECT setval('"public"."file_report_id_seq"', 3, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
ALTER SEQUENCE "public"."users_id_seq"
OWNED BY "public"."users"."id";
SELECT setval('"public"."users_id_seq"', 1, false);

-- ----------------------------
-- Primary Key structure for table file_report
-- ----------------------------
ALTER TABLE "public"."file_report" ADD CONSTRAINT "file_report_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table users
-- ----------------------------
ALTER TABLE "public"."users" ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");
