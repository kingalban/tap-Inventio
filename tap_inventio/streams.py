"""Stream type classes for tap-inventio."""

from __future__ import annotations

from tap_inventio.client import InventioStream

# All endpoints, aka 'types', defined for the inventio.it api
_ENDPOINTS = (
    "AccountScheduleNames-GET",
    "AccountScheduleResult-GET",
    "AccountingPeriod-GET",
    "BankAccount-GET",
    "CL-GET",
    "CashReceiptJournalList-GET",
    "ColumnLayoutNames-GET",
    "CompanyInformation-GET",
    "ConfigTemplateHeader-GET",
    "Currency-GET",
    "Customer-GET",
    "CustomerLedgerEntry-GET",
    "CustomerNumberList-GET",
    "CustomerPostingGroup-GET",
    "DeferralTemplates-GET",
    "DimensionMandatory-GET",
    "DimensionSetEntry-GET",
    "DimensionValue-GET",
    "GLAccount-GET",
    "GLBudgetEntry-GET",
    "GLEntry-GET",
    "GenBusinessPostingGroup-GET",
    "GenProductPostingGroup-GET",
    "GeneralJournal-GET",
    "GeneralJournalBatchName-GET",
    "GeneralJournalTemplateName-GET",
    "GeneralLedgerSetup-GET",
    "InventoryPostingGroup-GET",
    "Item-GET",
    "ItemCrossReference-GET",
    "ItemLedgerEntry-GET",
    "ItemPicture-GET",
    "ItemStock-GET",
    "ItemUnitOfMeasure-GET",
    "Job-GET",
    "JobTask-GET",
    "PaymentMethod-GET",
    "PaymentTerms-GET",
    "PurchOrder-GET",
    "PurchOrderLine-GET",
    "PurchasePrice-GET",
    "Resource-GET",
    "ResourceCost-GET",
    "ResourcePrice-GET",
    "SLD-GET",
    "SMARTexpense-GET",
    "SMARTexpenseApproval-GET",
    "SalesCrMem-GET",
    "SalesCrMemPDF-GET",
    "SalesInvoiceNumberList-GET",
    "SalesInvoiceOIOUBL-GET",
    "SalesInvoicePDF-GET",
    "SalesInvoices-GET",
    "SalesOrder-GET",
    "SalesOrderLine-GET",
    "SalesPrice-GET",
    "ShipmentMethod-GET",
    "UnitsOfMeasure-GET",
    "Variant-GET",
    "Vat-GET",
    "Vendor-GET",
    "VendorBankAcc-GET",
    "VendorLedgerEntry-GET",
    "VendorPostingGroup-GET",
    "Worktype-GET",
)


class GLEntryStream(InventioStream):
    """GLEntry-GET Stream."""

    name = "GLEntry"
    records_jsonpath = "$.entries.entry[*]"
    primary_keys = ("company_name", "entry_no")


class DimensionSetEntry(InventioStream):
    """DimensionSetEntry-GET Stream."""

    name = "DimensionSetEntry"
    records_jsonpath = "$.dimension-entries.dimension-entry[*]"
    primary_keys = ("company_name", "entry_no", "code")


class Customer(InventioStream):
    """Customer-GET Stream."""

    name = "Customer"
    records_jsonpath = "$.customers.customer[*]"
    primary_keys = ("company_name", "no")


STREAMS = [
    GLEntryStream,
    DimensionSetEntry,
    Customer,
]
