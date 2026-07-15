const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, LevelFormat, convertInchesToTwip
} = require("docx");

const PAGE_WIDTH_DXA = 12240;
const PAGE_HEIGHT_DXA = 15840;

function heading(text, level) {
  return new Paragraph({ text, heading: level, spacing: { before: 240, after: 120 } });
}

function body(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, ...opts })],
    spacing: { after: 160 },
  });
}

function bullet(text) {
  return new Paragraph({
    text,
    numbering: { reference: "bullet-list", level: 0 },
    spacing: { after: 80 },
  });
}

function makeCell(text, opts = {}) {
  return new TableCell({
    width: { size: opts.width || 2000, type: WidthType.DXA },
    shading: opts.header ? { type: ShadingType.CLEAR, fill: "1F4E5F" } : undefined,
    children: [new Paragraph({
      children: [new TextRun({ text, bold: !!opts.header, color: opts.header ? "FFFFFF" : "000000", size: 20 })],
    })],
  });
}

function simpleTable(headerRow, rows, colWidths) {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        children: headerRow.map((h, i) => makeCell(h, { header: true, width: colWidths[i] })),
        tableHeader: true,
      }),
      ...rows.map(r => new TableRow({
        children: r.map((c, i) => makeCell(c, { width: colWidths[i] })),
      })),
    ],
  });
}

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullet-list",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.35), hanging: convertInchesToTwip(0.2) } } } }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_WIDTH_DXA, height: PAGE_HEIGHT_DXA },
        margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 },
      },
    },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        children: [new TextRun({ text: "DATA MANAGEMENT PLAN", bold: true, size: 36, color: "1F4E5F" })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 40 },
        children: [new TextRun({
          text: "A Randomized, Placebo-Controlled Phase II Study to Evaluate the Efficacy and Safety of Rasnadi Compound (RC-101) in the Management of Knee Osteoarthritis",
          italics: true, size: 22,
        })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 300 },
        children: [new TextRun({ text: "Protocol No: RC101-OA-P2   |   Version 1.0   |   Illustrative / Educational Document", size: 18, color: "555555" })],
      }),

      heading("1. Purpose", HeadingLevel.HEADING_1),
      body("This Data Management Plan (DMP) defines the procedures, roles, and quality standards governing the collection, cleaning, validation, coding, and lock of clinical data for the RC-101 trial. It is written for an illustrative AYUSH/herbal Phase II trial and models the CDISC CDASH/SDTM-aligned data management practices common in conventional pharmaceutical trials, applied here to a traditional-medicine context where such standardization is not yet routine practice."),

      heading("2. Study Overview", HeadingLevel.HEADING_1),
      simpleTable(
        ["Item", "Detail"],
        [
          ["Study Drug", "Rasnadi Compound (RC-101) — polyherbal Ayurvedic formulation"],
          ["Indication", "Knee Osteoarthritis"],
          ["Design", "Randomized, double-blind, placebo-controlled, Phase II"],
          ["Sample Size", "80 subjects (40 per arm)"],
          ["Sites", "3 (SITE01, SITE02, SITE03)"],
          ["Visit Schedule", "Screening, Baseline, Week 2, 4, 8, 12, End of Study"],
          ["EDC Platform (modeled)", "REDCap-style electronic case report form"],
        ],
        [3200, 6300]
      ),

      heading("3. Data Flow", HeadingLevel.HEADING_1),
      body("Site staff enter source data into the eCRF at each visit. Data flows from the eCRF into the clinical database, where automated edit checks fire in real time. Data Management reviews system-generated queries daily; unresolved queries are routed to sites for clarification. Once queries are resolved and safety/reconciliation checks are complete, the domain is mapped to CDISC SDTM structure ahead of statistical analysis and database lock."),
      bullet("Site eCRF entry → Clinical database (raw/CRF-level domains)"),
      bullet("Automated validation pipeline → Query generation"),
      bullet("Site query resolution → Data correction / confirmation"),
      bullet("Safety reconciliation (AE ↔ Lab ↔ Concomitant Medication)"),
      bullet("SDTM mapping (DM, EX, VS, LB, AE, SUPPDM)"),
      bullet("Database lock → Statistical analysis (ADaM-ready)"),

      heading("4. Roles and Responsibilities", HeadingLevel.HEADING_1),
      simpleTable(
        ["Role", "Responsibility"],
        [
          ["Principal Investigator", "Ensures source data accuracy; responds to site queries; approves protocol deviations"],
          ["Clinical Research Coordinator (CRC)", "eCRF data entry; subject visit scheduling; query response coordination"],
          ["Data Manager", "Designs edit checks; runs validation pipeline; issues and tracks queries; maintains DMP"],
          ["Safety/Pharmacovigilance Reviewer", "Reviews AE/SAE data; confirms regulatory reporting timelines are met"],
          ["Biostatistician", "Defines SDTM/ADaM specifications; performs final analysis post database lock"],
        ],
        [3400, 6100]
      ),

      heading("5. Data Validation Approach", HeadingLevel.HEADING_1),
      body("Validation checks are grouped into four categories, executed via an automated Python pipeline against each incoming domain:"),
      bullet("Missing data checks — flags null/blank values in required fields"),
      bullet("Range and plausibility checks — protocol-defined ranges (e.g., age 35–75) and physiological bounds (e.g., systolic BP 70–200 mmHg)"),
      bullet("Logic checks — visit date sequencing relative to enrollment; AE onset vs. reporting timelines"),
      bullet("Cross-domain reconciliation — e.g., AE terms indicating hepatotoxicity cross-checked against Lab (ALT/AST) results"),
      body("All detected issues are logged in a query log with a unique Query ID, severity classification (Query / Protocol Deviation / Safety Signal / Critical / Regulatory Breach), and status tracked through to closure."),

      heading("6. Serious Adverse Event (SAE) Reporting", HeadingLevel.HEADING_1),
      body("Per Good Clinical Practice and AYUSH GCP (GCP-ASU) guidelines, all Serious Adverse Events must be reported to the sponsor/ethics committee within 24 hours of investigator awareness. The validation pipeline flags any SAE where the reported date exceeds the onset date by more than one day, escalating this as a Regulatory Breach requiring immediate Data Management and Safety review."),

      heading("7. Handling of AYUSH-Specific Data Elements", HeadingLevel.HEADING_1),
      body("This trial captures Ayurvedic constitutional typing (Prakriti: Vata, Pitta, Kapha, or dual/tridosha combinations) as a baseline characteristic. As CDISC SDTM has no native domain for this construct, it is captured via a supplemental qualifier domain (SUPPDM) linked to the parent DM domain, following standard CDISC extension conventions used when trial-specific or therapeutic-system-specific variables fall outside standard domains. Herbal dose form (tablet, churna, kashayam) and compliance percentage are similarly captured as domain-specific qualifiers alongside the standard EX (Exposure) variables."),

      heading("8. Database Lock Criteria", HeadingLevel.HEADING_1),
      bullet("All queries closed or formally documented as irresolvable with sponsor sign-off"),
      bullet("100% source data verification completed for critical variables (efficacy endpoints, SAEs)"),
      bullet("AE/Lab/Concomitant Medication reconciliation complete with no outstanding discrepancies"),
      bullet("SDTM domains finalized and mapping specification approved by Data Management and Biostatistics"),
      bullet("Final QC pass confirming no Critical or Regulatory Breach severity queries remain open"),

      heading("9. Quality Control Summary (This Dataset)", HeadingLevel.HEADING_1),
      body("As a demonstration of pipeline performance, the validation pipeline built for this project was run against a synthetic dataset with 41 deliberately embedded data quality issues spanning all domains (demographics, exposure, vital signs, labs, and adverse events). The pipeline achieved 100% detection of all seeded issues, in addition to identifying legitimate cross-domain reconciliation discrepancies not explicitly seeded. Full results are provided in the accompanying query log and validation summary report.", { italics: true }),

      heading("10. Regulatory and Ethical Framework (Reference)", HeadingLevel.HEADING_1),
      body("This illustrative DMP models data management practice consistent with: Good Clinical Practice for Ayurveda, Siddha and Unani (GCP-ASU) guidelines issued by the Ministry of AYUSH; ICMR National Ethical Guidelines for Biomedical and Health Research Involving Human Participants; CDISC CDASH and SDTM Implementation Guides; and ICH E6(R2) Good Clinical Practice, applied here to a traditional-medicine research context."),

      new Paragraph({ spacing: { before: 400 }, children: [new TextRun({ text: "— End of Document —", italics: true, color: "888888" })], alignment: AlignmentType.CENTER }),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  require("fs").writeFileSync("/home/claude/ayush_cdm_project/docs/Data_Management_Plan.docx", buffer);
  console.log("DMP docx written successfully.");
});
