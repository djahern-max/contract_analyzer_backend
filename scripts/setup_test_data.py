# setup_test_data.py - Create test project and contract
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal
from models.user import User
from models.project import Project
from models.contract import Contract
import json


def create_test_data():
    db = SessionLocal()
    try:
        # Check if we have a user, if not create one
        user = db.query(User).first()
        if not user:
            print("Creating test user...")
            user = User(
                email="test@example.com",
                hashed_password="fake_hashed_password",
                full_name="Test User",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created user: {user.email}")
        else:
            print(f"✅ Found existing user: {user.email}")

        # Check if we have a project, if not create one
        project = db.query(Project).filter(Project.user_id == user.id).first()
        if not project:
            print("Creating test project...")
            project = Project(
                user_id=user.id,
                name="Test Contract Analysis Project",
                description="Project for testing contract analysis functionality",
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            print(f"✅ Created project: {project.name}")
        else:
            print(f"✅ Found existing project: {project.name}")

        # Create a test contract
        print("Creating test contract...")
        test_contract_data = {
            "analysis": {
                "summary": {
                    "parties": ["ABC Construction Corp", "XYZ Property LLC"],
                    "contract_value": "$125,000",
                    "purpose": "Office renovation and electrical work",
                    "contract_type": "construction",
                    "start_date": "2024-03-01",
                    "completion_date": "2024-08-15",
                },
                "risks": {
                    "overall_risk_score": 65,
                    "high_risks": [
                        {
                            "risk": "No weather delay provisions",
                            "impact": "Schedule delays possible",
                            "recommendation": "Add weather clause",
                        }
                    ],
                    "medium_risks": [
                        {
                            "risk": "Change order process unclear",
                            "impact": "Potential cost overruns",
                            "recommendation": "Define change order approval process",
                        }
                    ],
                },
                "terms": {
                    "payment_schedule": "25% upfront, 50% at 50% completion, 25% final",
                    "penalty_clause": "$500 per day for delays",
                    "warranty_period": "2 years",
                },
            },
            "metadata": {
                "file_type": "pdf",
                "pages": 12,
                "processed_date": "2025-01-06",
                "processing_model": "test_setup",
            },
            "extracted_text": "Sample contract text for testing purposes...",
        }

        contract = Contract(
            project_id=project.id,
            file_name="test_construction_contract.pdf",
            file_url="https://your-spaces-url.com/contracts/test_contract.pdf",
            contract_data=test_contract_data,
            is_processed="completed",
        )

        db.add(contract)
        db.commit()
        db.refresh(contract)

        print(f"✅ Created contract: {contract.file_name} (ID: {contract.id})")
        print(
            f"   Contract value: {contract.contract_data['analysis']['summary']['contract_value']}"
        )
        print(
            f"   Risk score: {contract.contract_data['analysis']['risks']['overall_risk_score']}"
        )

        return user.id, project.id, contract.id

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        return None, None, None
    finally:
        db.close()


def test_contract_queries():
    db = SessionLocal()
    try:
        print("\n--- Testing Contract Queries ---")

        # Test 1: Basic contract retrieval
        contracts = db.query(Contract).all()
        print(f"Total contracts in database: {len(contracts)}")

        # Test 2: JSON query for contract value
        high_value_contracts = (
            db.query(Contract)
            .filter(
                Contract.contract_data["analysis"]["summary"][
                    "contract_value"
                ].astext.contains("$125,000")
            )
            .all()
        )
        print(f"Contracts with $125,000 value: {len(high_value_contracts)}")

        # Test 3: JSON query for parties
        abc_contracts = (
            db.query(Contract)
            .filter(
                Contract.contract_data["analysis"]["summary"][
                    "parties"
                ].astext.contains("ABC Construction")
            )
            .all()
        )
        print(f"Contracts with ABC Construction: {len(abc_contracts)}")

        # Test 4: Risk score query (fixed)
        from sqlalchemy import Integer

        risky_contracts = (
            db.query(Contract)
            .filter(
                Contract.contract_data["analysis"]["risks"][
                    "overall_risk_score"
                ].astext.cast(Integer)
                > 60
            )
            .all()
        )
        print(f"Contracts with risk score > 60: {len(risky_contracts)}")

        # Test 5: Show contract details
        if contracts:
            contract = contracts[0]
            print(f"\n--- Sample Contract Details ---")
            print(f"File: {contract.file_name}")
            print(
                f"Parties: {contract.contract_data['analysis']['summary']['parties']}"
            )
            print(
                f"Value: {contract.contract_data['analysis']['summary']['contract_value']}"
            )
            print(
                f"Risk Score: {contract.contract_data['analysis']['risks']['overall_risk_score']}"
            )
            print(
                f"High Risks: {len(contract.contract_data['analysis']['risks']['high_risks'])}"
            )

        print("\n✅ All database tests passed!")

    except Exception as e:
        print(f"❌ Query error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Setting up test data for contract analysis...")
    user_id, project_id, contract_id = create_test_data()

    if contract_id:
        print(f"\n✅ Test data created successfully!")
        print(f"   User ID: {user_id}")
        print(f"   Project ID: {project_id}")
        print(f"   Contract ID: {contract_id}")

        test_contract_queries()

        print(f"\n🎉 Database setup complete! You can now:")
        print(f"   - Analyze contracts and store results")
        print(f"   - Query contract data with JSON queries")
        print(f"   - Ready for Ollama integration")
    else:
        print("❌ Failed to create test data")
