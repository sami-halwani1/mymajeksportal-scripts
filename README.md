# mymajeksportal-scripts
MyMajeksPortal Backend Scripts and Functions

This repository contains Lambda functions, CloudFormation YAML templates, and various backend scripts used in the **MyMajeksPortal** backend infrastructure.

## 🔧 Purpose

These scripts power backend services and operations for **MyMajeksPortal**, including vendor and product management, image handling, and infrastructure automation.

## 📁 Structure

- `/lambda/` – AWS Lambda functions written in Python for handling backend logic.
- `/cloudformation/` – Infrastructure-as-Code templates for deploying backend resources.
- `/scripts/` – Utility scripts for automation, debugging, or data manipulation.

## ✅ Current Features

- **addNewVendors** – Adds new vendors to the database.
- **addProducts** – Adds new products tied to vendors.
- **addImages** – Uploads and associates image files to products in S3 and the DB.