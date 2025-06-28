# services/contract_analyzer.py
import aiohttp
import boto3
import json
import tempfile
import os
import PyPDF2
import asyncio
from typing import Dict, Any, Optional


class ContractAnalyzer:
    def __init__(self):
        # Digital Ocean Spaces client
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"https://{os.getenv('DO_SPACES_REGION')}.digitaloceanspaces.com",
            aws_access_key_id=os.getenv("DO_SPACES_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("DO_SPACES_SECRET_KEY"),
        )
        self.bucket_name = os.getenv("DO_SPACES_BUCKET_NAME")

        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_BASE_URL")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    async def analyze_contract_from_do_spaces(self, file_key: str) -> Dict[str, Any]:
        """Download contract from DO Spaces and analyze it"""

        print(f"🔍 Starting analysis of: {file_key}")

        try:
            # Step 1: Download file from Digital Ocean Spaces
            contract_text = await self._download_and_extract_text(file_key)
            print(f"✅ Downloaded and extracted text ({len(contract_text)} characters)")

            if len(contract_text.strip()) < 100:
                return {
                    "success": False,
                    "error": "Contract text too short - might be an image-based PDF or empty file",
                    "file_key": file_key,
                }

            # Step 2: Analyze with Ollama
            analysis_results = {}

            # Summary analysis
            print("📋 Running summary analysis...")
            summary = await self._analyze_with_ollama(contract_text, "summary")
            analysis_results["summary"] = summary

            # Risk analysis
            print("⚠️ Running risk analysis...")
            risks = await self._analyze_with_ollama(contract_text, "risks")
            analysis_results["risks"] = risks

            # Terms analysis
            print("📄 Running terms analysis...")
            terms = await self._analyze_with_ollama(contract_text, "terms")
            analysis_results["terms"] = terms

            print("✅ All analyses complete!")
            return {
                "success": True,
                "file_key": file_key,
                "analysis": analysis_results,
                "text_length": len(contract_text),
                "text_preview": (
                    contract_text[:500] + "..."
                    if len(contract_text) > 500
                    else contract_text
                ),
            }

        except Exception as e:
            print(f"❌ Error analyzing contract: {str(e)}")
            return {"success": False, "error": str(e), "file_key": file_key}

    async def _download_and_extract_text(self, file_key: str) -> str:
        """Download file from DO Spaces and extract text"""

        # Download to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            try:
                print(f"📥 Downloading {file_key}...")
                self.s3_client.download_file(self.bucket_name, file_key, temp_file.name)

                # Extract text based on file type
                if file_key.lower().endswith(".pdf"):
                    text = self._extract_pdf_text(temp_file.name)
                elif file_key.lower().endswith((".doc", ".docx")):
                    text = self._extract_docx_text(temp_file.name)
                else:
                    # Try as plain text
                    with open(
                        temp_file.name, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        text = f.read()

                return text

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                print(f"📄 PDF has {len(pdf_reader.pages)} pages")

                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        print(f"   Page {i+1}: {len(page_text)} characters")
                    except Exception as e:
                        print(f"   ⚠️ Could not extract page {i+1}: {e}")
                        continue

        except Exception as e:
            raise Exception(f"Failed to extract PDF text: {str(e)}")

        return text

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            import docx

            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            raise Exception("python-docx package required for DOCX files")
        except Exception as e:
            raise Exception(f"Failed to extract DOCX text: {str(e)}")

    async def _analyze_with_ollama(
        self, contract_text: str, analysis_type: str
    ) -> Dict[str, Any]:
        """Send contract text to Ollama for analysis"""

        # Truncate text if too long (Ollama has context limits)
        max_chars = 12000  # Conservative limit
        if len(contract_text) > max_chars:
            contract_text = (
                contract_text[:max_chars] + "\n\n[Text truncated for analysis]"
            )
            print(f"   ⚠️ Text truncated to {max_chars} characters")

        prompt = self._create_analysis_prompt(contract_text, analysis_type)

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent analysis
                        "num_predict": 1024,  # Reasonable response length
                        "top_p": 0.9,
                    },
                }

                print(f"   🤖 Sending to Ollama ({analysis_type})...")
                async with session.post(
                    f"{self.ollama_url}/api/generate", json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        parsed = self._parse_ollama_response(result.get("response", ""))
                        print(f"   ✅ {analysis_type} analysis complete")
                        return parsed
                    else:
                        error_text = await response.text()
                        raise Exception(
                            f"Ollama API error ({response.status}): {error_text}"
                        )

        except Exception as e:
            print(f"   ❌ Ollama error: {e}")
            return {"error": str(e), "analysis_type": analysis_type}

    def _create_analysis_prompt(self, contract_text: str, analysis_type: str) -> str:
        """Create analysis prompts for different types"""

        if analysis_type == "summary":
            return f"""
            Analyze this contract and extract key information. Return ONLY valid JSON:
            
            {contract_text}
            
            {{
                "contract_type": "type of contract",
                "parties": ["Party 1", "Party 2"],
                "contract_value": "amount or Not specified",
                "purpose": "main purpose", 
                "key_dates": ["date 1", "date 2"],
                "payment_terms": "payment info",
                "main_points": ["point 1", "point 2", "point 3"]
            }}
            """

        elif analysis_type == "risks":
            return f"""
            Identify risks in this contract. Return ONLY valid JSON:
            
            {contract_text}
            
            {{
                "overall_risk_level": "High/Medium/Low",
                "key_risks": ["risk 1", "risk 2", "risk 3"],
                "concerns": ["concern 1", "concern 2"],
                "recommendations": ["recommendation 1", "recommendation 2"]
            }}
            """

        elif analysis_type == "terms":
            return f"""
            Extract key contract terms. Return ONLY valid JSON:
            
            {contract_text}
            
            {{
                "payment_terms": "payment details",
                "deadlines": ["deadline 1", "deadline 2"],
                "penalties": ["penalty 1", "penalty 2"],
                "obligations": ["obligation 1", "obligation 2"],
                "termination": "termination conditions"
            }}
            """

        else:
            return f"Analyze this contract: {contract_text}"

    def _parse_ollama_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Ollama response"""
        try:
            # Find JSON in the response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1

            if start != -1 and end != -1:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                return {"raw_response": response_text, "parsed": False}

        except json.JSONDecodeError as e:
            return {"raw_response": response_text, "parsed": False, "error": str(e)}

    async def answer_question(
        self, contract_data: Dict[str, Any], question: str
    ) -> str:
        """Answer question about analyzed contract"""

        context = json.dumps(contract_data, indent=2)

        prompt = f"""
        Answer this question about a contract using the analysis data provided.
        
        Question: {question}
        
        Contract Analysis Data:
        {context}
        
        Provide a direct, helpful answer based on the analysis data.
        """

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 512},
                }

                async with session.post(
                    f"{self.ollama_url}/api/generate", json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "No answer generated")
                    else:
                        return f"Error: Could not get answer ({response.status})"

        except Exception as e:
            return f"Error: {str(e)}"
