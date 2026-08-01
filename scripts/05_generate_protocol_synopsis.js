const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, LevelFormat
} = require("docx");

const PAGE_WIDTH_DXA = 12240;
const PAGE_HEIGHT_DXA = 15840;

function heading(text, level) {
  return new Paragraph({ text, heading: level, spacing: { before: 200, after: 100 } });
}
function body(text, opts = {}) {
  return new Paragraph({ children: [new TextRun({ text, ...opts })], spacing: { after: 140 } });
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
      new TableRow({ children: headerRow.map((h, i) => makeCell(h, { header: true, width: colWidths[i] })), tableHeader: true }),
      ...rows.map(r => new TableRow({ children: r.map((c, i) => makeCell(c, { width: colWidths[i] })) })),
    ],
  });
}

const doc = new Document({
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
        children: [new TextRun({ text: "PROTOCOL SYNOPSIS", bold: true, size: 32, color: "1F4E5F" })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 260 },
        children: [new TextRun({ text: "Protocol No: RC101-OA-P2   |   Illustrative / Educational Document", size: 18, color: "555555" })],
      }),

      heading("Title", HeadingLevel.HEADING_1),
      body("A Randomized, Placebo-Controlled Phase II Study to Evaluate the Efficacy and Safety of Rasnadi Compound (RC-101) in the Management of Knee Osteoarthritis."),

      heading("Rationale", HeadingLevel.HEADING_1),
      body("Knee osteoarthritis is a chronic degenerative joint condition with substantial symptom burden and limited disease-modifying options in conventional care. Rasnadi-type polyherbal Ayurvedic formulations have a long traditional-use history for joint disorders (Sandhivata). This study evaluates a standardized formulation, RC-101, under a randomized controlled design consistent with GCP-ASU and ICH E6(R2) principles, generating data suitable for CDISC-aligned data management."),

      heading("Objectives", HeadingLevel.HEADING_1),
      body("Primary: To evaluate the efficacy of RC-101 versus placebo in reducing knee osteoarthritis symptom severity over 12 weeks, as measured by a validated pain and function scale.", { bold: false }),
      body("Secondary: To assess the safety and tolerability of RC-101, including hepatic safety, over the treatment period; to characterize compliance with the assigned dose form; to explore association between baseline Prakriti (constitutional type) and treatment response."),

      heading("Study Design", HeadingLevel.HEADING_1),
      simpleTable(
        ["Parameter", "Detail"],
        [
          ["Design", "Randomized, double-blind, placebo-controlled, parallel-group, Phase II"],
          ["Sample size", "80 subjects (40 RC-101, 40 Placebo), 1:1 allocation"],
          ["Sites", "3 sites (SITE01, SITE02, SITE03)"],
          ["Treatment duration", "12 weeks, with End of Study visit at Week 12/Day 90"],
          ["Visit schedule", "Screening (Day -14), Baseline (Day 0), Week 2, Week 4, Week 8, Week 12, End of Study"],
          ["Investigational product", "Rasnadi Compound (RC-101), dose forms: Tablet (500 mg), Churna/Kashayam (1000-1500 mg equivalent)"],
        ],
        [3000, 6500]
      ),

      heading("Population", HeadingLevel.HEADING_1),
      body("Key inclusion criteria: Age 35-75 years; clinically and radiologically confirmed knee osteoarthritis (Kellgren-Lawrence Grade II-III); willing and able to provide informed consent."),
      body("Key exclusion criteria: Prior joint replacement surgery on the study knee; concurrent use of disease-modifying osteoarthritis drugs; clinically significant hepatic or renal impairment at screening; pregnancy or lactation."),

      heading("Endpoints", HeadingLevel.HEADING_1),
      body("Primary endpoint: Change from baseline to Week 12 in WOMAC (Western Ontario and McMaster Universities Osteoarthritis Index) composite score."),
      body("Safety endpoints: Incidence and severity of adverse events; changes in liver function tests (ALT, AST); vital signs; incidence of Serious Adverse Events with regulatory-timeline reporting compliance."),
      body("Exploratory endpoint: Plasma level of a defined phytochemical marker compound as a pharmacokinetic/exposure indicator; association between Prakriti type and WOMAC response."),

      heading("Data Management Approach (Reference)", HeadingLevel.HEADING_1),
      body("Data collected under this protocol is managed per the accompanying Data Management Plan, including CDISC SDTM-aligned domain structuring (DM, EX, VS, LB, AE, and a supplemental SUPPDM domain for the AYUSH-specific Prakriti variable), automated validation checks, and AE/SAE reconciliation procedures."),

      heading("Ethical and Regulatory Framework", HeadingLevel.HEADING_1),
      body("Conducted in accordance with Good Clinical Practice for Ayurveda, Siddha and Unani (GCP-ASU, Ministry of AYUSH), ICMR National Ethical Guidelines for Biomedical and Health Research Involving Human Participants, and ICH E6(R2) Good Clinical Practice. Registration with the Clinical Trials Registry of India (CTRI) and Institutional Ethics Committee approval are prerequisites for enrollment (illustrative; not actually registered)."),

      new Paragraph({ spacing: { before: 300 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "— End of Document —", italics: true, color: "888888" })] }),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  require("fs").writeFileSync("/home/claude/ayush_cdm_project/docs/Protocol_Synopsis.docx", buffer);
  console.log("Protocol synopsis docx written successfully.");
});
