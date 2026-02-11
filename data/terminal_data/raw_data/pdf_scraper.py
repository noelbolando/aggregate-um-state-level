#!/usr/bin/env python3
"""
ACA PDF Scraper
Extracts company and terminal information from American Cement Association state one-sheets
"""

import re
from pypdf import PdfReader
from pathlib import Path
import csv
import json
from typing import List, Dict
import sys


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def extract_state_name(text: str) -> str:
    """Extract the state name from the document."""
    # Look for pattern like "ALABAMA:" at the start
    match = re.search(r'^([A-Z\s]+):\s*\n', text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "Unknown"


def extract_companies(text: str) -> List[Dict[str, str]]:
    """
    Extract company information from the PDF text.
    Returns a list of dictionaries with company, location, and house_member.
    """
    companies = []
    
    # Find the COMPANY LOCATION HOUSE MEMBERS section
    company_section_match = re.search(
        r'COMPANY\s+LOCATION\s+HOUSE\s+MEMBERS\s*\n(.*?)(?=PLANT\s+LOCATIONS|$)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    
    if not company_section_match:
        print("Warning: Could not find COMPANY LOCATION HOUSE MEMBERS section", file=sys.stderr)
        return companies
    
    company_section = company_section_match.group(1).strip()
    
    # Strategy: Look for lines that contain representative pattern
    # Accumulate any continuation lines (like "of Alabama, Inc.")
    lines = company_section.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # Check if this line contains a representative (has party-district pattern)
        rep_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+\(([RD])-(\d+(?:st|nd|rd|th))\)\s*$', line)
        
        if rep_match:
            # This line contains the representative
            rep_name = rep_match.group(1).strip()
            party = rep_match.group(2)
            district = rep_match.group(3)
            house_member = f"{rep_name} ({party}-{district})"
            
            # Everything before the representative is company and location
            before_rep = line[:rep_match.start()].strip()
            
            # Check if next line is a continuation (starts with lowercase or "of")
            company_suffix = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # If next line starts with "of" or lowercase, it's probably a continuation
                if next_line and (next_line.startswith('of ') or (next_line[0].islower() if next_line else False)):
                    company_suffix = " " + next_line
                    i += 1  # Skip the next line since we've consumed it
            
            # Parse company and location from before_rep
            # Strategy: Location is typically a single capitalized word before the representative
            # Look for pattern: [Company words...] [Location word] [Representative]
            parts = before_rep.split()
            
            if len(parts) >= 2:
                # Last word is likely the location
                location = parts[-1]
                company = ' '.join(parts[:-1]) + company_suffix
            elif len(parts) == 1:
                company = parts[0] + company_suffix
                location = ""
            else:
                company = before_rep + company_suffix
                location = ""
            
            companies.append({
                'company': company.strip(),
                'location': location.strip(),
                'house_member': house_member
            })
        
        i += 1
    
    return companies


def extract_terminals(text: str) -> List[Dict[str, str]]:
    """
    Extract terminal information from the PDF text.
    Returns a list of dictionaries with company, location, and house_member.
    """
    terminals = []
    
    # Find the PLANT LOCATIONS TERMINALS section  
    terminal_section_match = re.search(
        r'PLANT\s+LOCATIONS\s+TERMINALS\s*\n(.*?)(?=Locations\s+with\s+terminals|American\s+Cement|For\s+more\s+information|$)',
        text,
        re.DOTALL | re.IGNORECASE
    )
    
    if not terminal_section_match:
        print("Warning: Could not find PLANT LOCATIONS TERMINALS section", file=sys.stderr)
        return terminals
    
    terminal_section = terminal_section_match.group(1).strip()
    
    # Terminals have format: Company, Location, Representative (Party-District)
    # They're comma-separated which makes them easier to parse
    pattern = r'([^,\n]+),\s*([^,]+),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+\(([RD])-(\d+(?:st|nd|rd|th))\)'
    
    matches = re.finditer(pattern, terminal_section)
    
    for match in matches:
        company = match.group(1).strip()
        location = match.group(2).strip()
        rep_name = match.group(3).strip()
        party = match.group(4)
        district = match.group(5)
        house_member = f"{rep_name} ({party}-{district})"
        
        terminals.append({
            'company': company,
            'location': location,
            'house_member': house_member
        })
    
    return terminals


def scrape_pdf(pdf_path: str) -> Dict:
    """
    Scrape a single PDF and return the extracted data.
    """
    text = extract_text_from_pdf(pdf_path)
    state = extract_state_name(text)
    companies = extract_companies(text)
    terminals = extract_terminals(text)
    
    return {
        'state': state,
        'pdf_path': pdf_path,
        'companies': companies,
        'terminals': terminals
    }


def scrape_multiple_pdfs(pdf_paths: List[str]) -> List[Dict]:
    """
    Scrape multiple PDFs and return all extracted data.
    """
    results = []
    for pdf_path in pdf_paths:
        print(f"Processing: {pdf_path}")
        try:
            result = scrape_pdf(pdf_path)
            results.append(result)
            print(f"  Found {len(result['companies'])} companies and {len(result['terminals'])} terminals")
        except Exception as e:
            print(f"  Error processing {pdf_path}: {e}", file=sys.stderr)
    return results


def save_to_csv(results: List[Dict], output_dir: str = "."):
    """
    Save results to a single CSV file with both companies and terminals.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to single combined CSV
    combined_file = output_dir / "aca_data.csv"
    with open(combined_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['State', 'Type', 'Company', 'Location', 'House Member'])
        
        for result in results:
            state = result['state']
            
            # Write companies
            for company in result['companies']:
                writer.writerow([
                    state,
                    'Company',
                    company['company'],
                    company['location'],
                    company['house_member']
                ])
            
            # Write terminals
            for terminal in result['terminals']:
                writer.writerow([
                    state,
                    'Terminal',
                    terminal['company'],
                    terminal['location'],
                    terminal['house_member']
                ])
    
    print(f"Saved combined data to: {combined_file}")


def save_to_json(results: List[Dict], output_dir: str = "."):
    """
    Save results to a JSON file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_file = output_dir / "aca_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Saved JSON data to: {json_file}")


def main():
    """
    Main function to run the scraper.
    """
    import argparse
    import glob
    
    parser = argparse.ArgumentParser(description='Scrape ACA PDF one-sheets for company and terminal information')
    parser.add_argument('pdfs', nargs='*', help='PDF files to process (optional - will auto-detect ACA*.pdf if not provided)')
    parser.add_argument('-o', '--output-dir', default='.', help='Output directory for CSV/JSON files (default: current directory)')
    parser.add_argument('--csv', action='store_true', help='Output to CSV files')
    parser.add_argument('--json', action='store_true', help='Output to JSON file')
    parser.add_argument('--both', action='store_true', help='Output to both CSV and JSON')
    
    args = parser.parse_args()
    
    # If no PDFs specified, find all ACA*.pdf files in the script's directory
    if not args.pdfs:
        script_dir = Path(__file__).parent.resolve()
        pdf_pattern = script_dir / "ACA*.pdf"
        args.pdfs = glob.glob(str(pdf_pattern))
        
        if not args.pdfs:
            print("No PDF files specified and no ACA*.pdf files found in script directory.")
            print("Usage: python3 scrape_aca_pdfs.py [pdf_files...]")
            sys.exit(1)
        
        print(f"Auto-detected {len(args.pdfs)} ACA PDF(s) in script directory:")
        for pdf in sorted(args.pdfs):
            print(f"  - {Path(pdf).name}")
        print()
    
    # If no output format specified, default to both
    if not args.csv and not args.json and not args.both:
        args.both = True
    
    # Scrape PDFs
    results = scrape_multiple_pdfs(args.pdfs)
    
    # Save results
    if args.csv or args.both:
        save_to_csv(results, args.output_dir)
    
    if args.json or args.both:
        save_to_json(results, args.output_dir)
    
    # Print summary
    print(f"\n=== Summary ===")
    total_companies = sum(len(r['companies']) for r in results)
    total_terminals = sum(len(r['terminals']) for r in results)
    print(f"Processed {len(results)} PDFs")
    print(f"Total companies: {total_companies}")
    print(f"Total terminals: {total_terminals}")


if __name__ == '__main__':
    main()
    