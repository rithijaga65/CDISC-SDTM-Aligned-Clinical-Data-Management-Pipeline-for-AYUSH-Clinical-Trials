const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, PageBreak
} = require("docx");

const PAGE_WIDTH_DXA = 12240;
const PAGE_HEIGHT_DXA = 15840;

function heading(text, level) {
  return new Paragraph({ text, heading: level, spacing: { before: 200, after: 100 } });
}
function body(text, opts = {}) {
  return new Paragraph({ children: [new TextRun({ text, ...opts })], spacing: { after: 120 } });
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
function crfTable(headerRow, rows, colWidths) {
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
function pageBreak() { return new Paragraph({ children: [new PageBreak()] }); }
function crfHeader(title, cdashDomain) {
  return [
    new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: title, bold: true, size: 26, color: "1F4E5F" })] }),
    new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: `CDASH Domain: ${cdashDomain}   |   Study RC101-OA-P2`, size: 18, color: "555555", italics: true })] }),
  ];
}

const doc = new Document({
  sections: [{
    properties: { page: { size: { width: PAGE_WIDTH_DXA, height: PAGE_HEIGHT_DXA }, margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: "CASE REPORT FORMS (CRF TEMPLATES)", bold: true, size: 32, color: "1F4E5F" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 }, children: [new TextRun({ text: "Protocol RC101-OA-P2   |   Illustrative / Educational Document", size: 18, color: "555555" })] }),

      ...crfHeader("1. Demographics (DM)", "DM"),
      crfTable(["Field", "Type", "Notes"], [
        ["Subject ID", "Text", "Auto-generated, format AYU-0nn"],
        ["Site ID", "Dropdown", "SITE01 / SITE02 / SITE03"],
        ["Date of Informed Consent", "Date", "dd-mmm-yyyy"],
        ["Date of Birth / Age", "Number", "Years; protocol range 35-75"],
        ["Sex", "Radio button", "Male / Female"],
        ["Prakriti (Constitutional Type)", "Dropdown", "Vata / Pitta / Kapha / Vata-Pitta / Pitta-Kapha / Tridosha — assessed by qualified Ayurvedic physician"],
        ["Enrollment Date", "Date", "dd-mmm-yyyy"],
      ], [3400, 1800, 3300]),

      ...crfHeader("2. Study Drug Exposure / Dosing (EX)", "EX"),
      crfTable(["Field", "Type", "Notes"], [
        ["Visit", "Dropdown", "Baseline / Week 2 / Week 4 / Week 8 / Week 12"],
        ["Dose Form Dispensed", "Dropdown", "Tablet / Churna (Powder) / Kashayam (Decoction)"],
        ["Planned Dose (mg)", "Number", "Per protocol dosing schedule"],
        ["Returned Units / Compliance", "Number (%)", "Calculated from dispensed vs. returned count"],
      ], [3400, 1800, 3300]),

      ...crfHeader("3. Vital Signs (VS)", "VS"),
      crfTable(["Field", "Type", "Notes"], [
        ["Visit / Visit Date", "Dropdown / Date", "Per visit schedule"],
        ["Systolic BP (mmHg)", "Number", "Plausible range 70-200"],
        ["Diastolic BP (mmHg)", "Number", "Plausible range 40-120"],
        ["Heart Rate (bpm)", "Number", "Plausible range 40-140"],
        ["Temperature (°C)", "Number", "Record in Celsius only"],
        ["Weight (kg)", "Number", "Measured in light clothing, no shoes"],
      ], [3400, 1800, 3300]),

      pageBreak(),

      ...crfHeader("4. Laboratory Values (LB)", "LB"),
      crfTable(["Field", "Type", "Notes"], [
        ["Visit", "Dropdown", "Screening / Baseline / Week 4 / Week 8 / Week 12"],
        ["ALT (U/L)", "Number", "Flag if >120 U/L (>3x ULN) for hepatic safety review"],
        ["AST (U/L)", "Number", "Standard reference range applies"],
        ["Creatinine (mg/dL)", "Number", "Must be a positive value"],
        ["hs-CRP (mg/L)", "Number", "Inflammation marker"],
        ["Phytochemical Marker Compound (ng/mL)", "Number", "Non-standard analyte specific to RC-101; custom LBTESTCD at SDTM mapping"],
      ], [3400, 1800, 3300]),

      ...crfHeader("5. Adverse Events (AE)", "AE"),
      crfTable(["Field", "Type", "Notes"], [
        ["AE Term", "Text", "Verbatim term, coded at data management stage"],
        ["Onset Date / Study Day", "Date / Number", "Relative to enrollment date"],
        ["Severity", "Dropdown", "Mild / Moderate / Severe"],
        ["Serious (Y/N)", "Radio button", "Per ICH E2A seriousness criteria"],
        ["Relationship to Study Drug", "Dropdown", "Related / Possibly Related / Not Related"],
        ["Outcome", "Dropdown", "Resolved / Resolving / Ongoing"],
        ["Date Reported to Sponsor", "Date", "SAEs: must be within 24 hours of investigator awareness"],
      ], [3400, 1800, 3300]),

      ...crfHeader("6. Concomitant Medications (CM)", "CM"),
      crfTable(["Field", "Type", "Notes"], [
        ["Medication Name", "Text", "Generic name preferred"],
        ["Start Date", "Date", "Relative to enrollment"],
        ["Ongoing (Y/N)", "Radio button", "If N, end date required"],
      ], [3400, 1800, 3300]),

      new Paragraph({ spacing: { before: 300 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "— End of Document —", italics: true, color: "888888" })] }),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  require("fs").writeFileSync("/home/claude/ayush_cdm_project/docs/CRF_Templates.docx", buffer);
  console.log("CRF templates docx written successfully.");
});
