# test_contract_db.py - Run this to test your new table
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal
from models.contract import Contract
from models.project import Project
import json


def test_contract_creation():
    db = SessionLocal()
    try:
        # Get an existing project (or create one for testing)
        project = db.query(Project).first()
        if not project:
            print("No projects found. Create a project first.")
            return

        # Create a test contract
        test_contract_data = {
            "analysis": {
                "summary": {
                    "parties": ["Test Company A", "Test Company B"],
                    "contract_value": "$50,000",
                    "purpose": "Test contract for system verification",
                }
            },
            "metadata": {"file_type": "pdf", "pages": 5},
        }

        contract = Contract(
            project_id=project.id,
            file_name="test_contract.pdf",
            file_url="https://example.com/test_contract.pdf",
            contract_data=test_contract_data,
            is_processed="completed",
        )

        db.add(contract)
        db.commit()
        db.refresh(contract)

        print(f"✅ Contract created successfully with ID: {contract.id}")
        print(f"   Project: {project.name}")
        print(f"   File: {contract.file_name}")
        print(f"   Data: {contract.contract_data}")

        # Test querying the JSON data
        result = (
            db.query(Contract)
            .filter(
                Contract.contract_data["analysis"]["summary"]["contract_value"].astext
                == "$50,000"
            )
            .first()
        )

        if result:
            print(
                f"✅ JSON query test passed - found contract with value: {result.contract_data['analysis']['summary']['contract_value']}"
            )
        else:
            print("❌ JSON query test failed")

        return contract.id

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def test_contract_queries():
    db = SessionLocal()
    try:
        # Test various JSON queries
        print("\n--- Testing JSON Queries ---")

        # Query 1: Find contracts by party name
        contracts_with_party = (
            db.query(Contract)
            .filter(
                Contract.contract_data["analysis"]["summary"][
                    "parties"
                ].astext.contains("Test Company A")
            )
            .all()
        )
        print(f"Contracts with 'Test Company A': {len(contracts_with_party)}")

        # Query 2: Find contracts by value
        high_value_contracts = (
            db.query(Contract)
            .filter(
                Contract.contract_data["analysis"]["summary"][
                    "contract_value"
                ].astext.contains("$50,000")
            )
            .all()
        )
        print(f"Contracts with $50,000 value: {len(high_value_contracts)}")

        # Query 3: Get all processed contracts
        processed_contracts = (
            db.query(Contract).filter(Contract.is_processed == "completed").all()
        )
        print(f"Processed contracts: {len(processed_contracts)}")

        print("✅ All query tests passed!")

    except Exception as e:
        print(f"❌ Query error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Testing contract database setup...")
    contract_id = test_contract_creation()
    if contract_id:
        test_contract_queries()
