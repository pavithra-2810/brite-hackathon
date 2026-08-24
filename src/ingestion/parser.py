"""
Clause-Preserving Ingestion Parser
Parses Markdown policy manuals and amendments into structured Clause objects.
"""

import re
from typing import List, Dict, Any, Optional
from src.policy.models import Clause


class PolicyIngestor:
    def __init__(self):
        pass

    def parse_policy_manual(
        self, content: str, document_name: str = "policy-manual.md", policy_version: str = "2025-12-31"
    ) -> List[Clause]:
        clauses: List[Clause] = []
        
        current_part = "General Policy"
        current_section = ""
        current_section_title = ""
        
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Match Part headers: # Part 1 — Scope and Definitions
            part_match = re.match(r"^#\s+(Part\s+\d+.*)$", line, re.IGNORECASE)
            if part_match:
                current_part = part_match.group(1).strip()
                i += 1
                continue
                
            # Match Section headers: ## 1.1 Purpose of the Program
            sec_match = re.match(r"^##\s+(\d+\.\d+)\s+(.*)$", line)
            if sec_match:
                current_section = f"§{sec_match.group(1)}"
                current_section_title = sec_match.group(2).strip()
                i += 1
                continue
            
            # Match numbered paragraphs: **1.1.1** Text... or **6.4.1**
            clause_match = re.match(r"^\*\*(\d+\.\d+\.\d+)\*\*\s*(.*)$", line)
            if clause_match:
                sec_num = clause_match.group(1)
                clause_id = f"§{sec_num}"
                body_text = clause_match.group(2).strip()
                
                # Check if sub-items follow (a), (b), (c)...
                j = i + 1
                sub_items = []
                table_lines = []
                while j < len(lines):
                    next_line = lines[j].strip()
                    if re.match(r"^\*\*(\d+\.\d+\.\d+)\*\*", next_line) or re.match(r"^##?\s+", next_line):
                        break
                    if re.match(r"^\([a-z]\)", next_line):
                        sub_items.append(next_line)
                    elif next_line.startswith("|") and next_line.endswith("|"):
                        table_lines.append(next_line)
                    elif next_line and not next_line.startswith("---"):
                        body_text += " " + next_line
                    elif next_line.startswith("---"):
                        break
                    j += 1
                
                full_text = body_text
                if table_lines:
                    full_text += "\n" + "\n".join(table_lines)
                
                # Parent section e.g. §6.4 from §6.4.1
                parent_sec_num = ".".join(sec_num.split(".")[:2])
                parent_sec_id = f"§{parent_sec_num}"
                
                # Create main clause
                clause = Clause(
                    clause_id=clause_id,
                    part_id=current_part,
                    section_title=current_section_title,
                    text=full_text,
                    full_path=f"{current_part} > {current_section} {current_section_title} > {clause_id}",
                    document=document_name,
                    policy_version=policy_version,
                    effective_from="2025-12-31",
                    effective_to=None,
                    parent_section=parent_sec_id,
                    referenced_sections=self._extract_references(full_text)
                )
                clauses.append(clause)
                
                # Also create explicit sub-item clauses if (a), (b) exist
                for item in sub_items:
                    item_match = re.match(r"^\(([a-z])\)\s*(.*)$", item)
                    if item_match:
                        sub_letter = item_match.group(1)
                        sub_clause_id = f"{clause_id}({sub_letter})"
                        sub_clause = Clause(
                            clause_id=sub_clause_id,
                            part_id=current_part,
                            section_title=current_section_title,
                            text=f"{sub_clause_id}: {item_match.group(2)}",
                            full_path=f"{current_part} > {current_section} {current_section_title} > {sub_clause_id}",
                            document=document_name,
                            policy_version=policy_version,
                            effective_from="2025-12-31",
                            effective_to=None,
                            parent_section=clause_id,
                            referenced_sections=self._extract_references(item)
                        )
                        clauses.append(sub_clause)
                
                i = j
                continue
                
            i += 1
            
        return clauses

    def parse_amendment(
        self, content: str, document_name: str = "Amendment No. 2026-01.md", policy_version: str = "2026-03-01"
    ) -> List[Clause]:
        clauses: List[Clause] = []
        lines = content.splitlines()
        
        current_header = "Amendment No. 2026-01"
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("## "):
                current_header = line.replace("## ", "").strip()
                i += 1
                continue
            
            # Match paragraphs like **1.1** In §6.4.1(a)... or **4.2** After §10.5.3...
            para_match = re.match(r"^\*\*(\d+\.\d+)\*\*\s*(.*)$", line)
            if para_match:
                para_id = f"Amendment-2026-01-§{para_match.group(1)}"
                body = para_match.group(2).strip()
                
                # Check for tables or additional lines
                j = i + 1
                table_lines = []
                while j < len(lines):
                    next_line = lines[j].strip()
                    if re.match(r"^\*\*(\d+\.\d+)\*\*", next_line) or next_line.startswith("## "):
                        break
                    if next_line.startswith("|") and next_line.endswith("|"):
                        table_lines.append(next_line)
                    elif next_line and not next_line.startswith("---") and not next_line.startswith("*"):
                        body += " " + next_line
                    j += 1
                    
                if table_lines:
                    body += "\n" + "\n".join(table_lines)
                    
                refs = self._extract_references(body)
                clause = Clause(
                    clause_id=para_id,
                    part_id="Amendment No. 2026-01",
                    section_title=current_header,
                    text=body,
                    full_path=f"Amendment No. 2026-01 > {current_header} > {para_id}",
                    document=document_name,
                    policy_version=policy_version,
                    effective_from="2026-03-01",
                    effective_to=None,
                    parent_section="Amendment No. 2026-01",
                    referenced_sections=refs
                )
                clauses.append(clause)
                i = j
                continue
            i += 1
            
        return clauses

    def _extract_references(self, text: str) -> List[str]:
        # Extract matches like §6.4.1, §4.3.2, §10.5
        refs = re.findall(r"§\d+(?:\.\d+)+(?:\([a-z]\))?", text)
        return list(set(refs))
