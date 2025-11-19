from fastapi import APIRouter, Query, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, timedelta
import uuid
import csv
import io

from app.db.base import get_db
from app.core.deps import get_current_user, get_current_tenant
from app.models.user import User
from app.models.tenant import Tenant
from app.models.aws_account import AWSAccount
from app.services.cost_service import CostService

router = APIRouter()


class CostBreakdownItem(BaseModel):
    service: str
    cost: float
    percentage: float


class CostSummaryResponse(BaseModel):
    total_cost: float
    currency: str
    start_date: str
    end_date: str
    breakdown: List[CostBreakdownItem]


class CostTrendItem(BaseModel):
    date: str
    cost: float


@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get cost summary for the specified period

    - Defaults to last 30 days if no dates provided
    - Groups costs by service
    - Shows percentage breakdown
    """
    # Set default dates if not provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Validate dates
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )

    # Initialize cost service
    cost_service = CostService(db)

    # Get cost summary
    summary = await cost_service.get_cost_summary(
        tenant_id=str(current_tenant.id),
        start_date=start_date,
        end_date=end_date,
        aws_account_id=account_id
    )

    return summary


@router.get("/trend", response_model=List[CostTrendItem])
async def get_cost_trend(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get daily cost trend for the specified period

    - Returns time series data for charting
    - Defaults to last 30 days
    """
    # Set default dates
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    cost_service = CostService(db)

    trend = await cost_service.get_cost_trend(
        tenant_id=str(current_tenant.id),
        start_date=start_date,
        end_date=end_date,
        aws_account_id=account_id
    )

    return trend


@router.post("/sync/{account_id}")
async def sync_cost_data(
    account_id: uuid.UUID,
    days: int = Query(30, description="Number of days to sync", ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Manually trigger cost data sync for an AWS account

    - Fetches data from AWS Cost Explorer
    - Stores in database for fast queries
    - Default: last 30 days
    """
    # Get AWS account
    aws_account = db.query(AWSAccount).filter(
        AWSAccount.id == account_id,
        AWSAccount.tenant_id == current_tenant.id
    ).first()

    if not aws_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS account not found"
        )

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Update sync status
    aws_account.sync_status = "syncing"
    db.commit()

    # Fetch costs
    cost_service = CostService(db)
    result = await cost_service.fetch_costs_for_account(
        aws_account=aws_account,
        start_date=start_date,
        end_date=end_date
    )

    return result


@router.get("/by-region", response_model=CostSummaryResponse)
async def get_cost_by_region(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get cost breakdown by AWS region

    - Defaults to last 30 days if no dates provided
    - Groups costs by region
    - Shows percentage breakdown
    """
    # Set default dates
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    cost_service = CostService(db)

    breakdown = await cost_service.get_cost_by_region(
        tenant_id=str(current_tenant.id),
        start_date=start_date,
        end_date=end_date,
        aws_account_id=account_id
    )

    return breakdown


class MonthComparisonResponse(BaseModel):
    current_month: dict
    previous_month: dict
    change: dict
    currency: str


@router.get("/month-comparison", response_model=MonthComparisonResponse)
async def get_month_comparison(
    current_month_start: Optional[date] = None,
    current_month_end: Optional[date] = None,
    account_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Compare current month costs with previous month

    - Defaults to current month if dates not provided
    - Shows change amount and percentage
    - Indicates trend direction
    """
    # Default to current month
    if not current_month_start:
        today = date.today()
        current_month_start = date(today.year, today.month, 1)
    if not current_month_end:
        current_month_end = date.today()

    cost_service = CostService(db)

    comparison = await cost_service.get_month_over_month_comparison(
        tenant_id=str(current_tenant.id),
        current_month_start=current_month_start,
        current_month_end=current_month_end,
        aws_account_id=account_id
    )

    return comparison


class ForecastResponse(BaseModel):
    success: bool
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_forecast: Optional[float] = None
    currency: Optional[str] = None
    forecast: Optional[List[CostTrendItem]] = None
    error: Optional[str] = None


@router.get("/forecast/{account_id}", response_model=ForecastResponse)
async def get_cost_forecast(
    account_id: uuid.UUID,
    days: int = Query(30, description="Number of days to forecast", ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get cost forecast from AWS Cost Explorer

    - Uses AWS Cost Explorer forecasting
    - Default: 30 days ahead
    - Requires active AWS account
    """
    # Get AWS account
    aws_account = db.query(AWSAccount).filter(
        AWSAccount.id == account_id,
        AWSAccount.tenant_id == current_tenant.id
    ).first()

    if not aws_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS account not found"
        )

    # Calculate forecast date range
    start_date = date.today()
    end_date = start_date + timedelta(days=days)

    cost_service = CostService(db)
    forecast = await cost_service.get_cost_forecast(
        aws_account=aws_account,
        start_date=start_date,
        end_date=end_date
    )

    return forecast


@router.get("/export/csv")
async def export_costs_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Export cost data to CSV format

    - Returns CSV file with detailed cost breakdown
    - Includes date, service, region, and cost columns
    """
    # Set default dates
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Query cost data
    from app.models.cost_data import CostData

    query = db.query(CostData).filter(
        CostData.tenant_id == current_tenant.id,
        CostData.date >= start_date,
        CostData.date <= end_date
    )

    if account_id:
        query = query.filter(CostData.aws_account_id == account_id)

    cost_records = query.order_by(CostData.date.desc()).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Date', 'Service', 'Region', 'Cost', 'Currency'])

    # Write data
    for record in cost_records:
        writer.writerow([
            record.date.isoformat(),
            record.service,
            record.region,
            f"{record.cost:.2f}",
            record.currency
        ])

    # Prepare response
    output.seek(0)
    filename = f"cloudcostly_costs_{start_date}_{end_date}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


class RecommendationItem(BaseModel):
    id: str
    type: str
    category: str
    severity: str
    title: str
    description: str
    resource: Optional[str] = None
    current_config: Optional[str] = None
    recommended_config: Optional[str] = None
    potential_savings: float
    savings_currency: str = "USD"
    action: Optional[str] = None
    effort: Optional[str] = None
    finding: Optional[str] = None


class RecommendationsResponse(BaseModel):
    total_recommendations: int
    total_potential_savings: float
    currency: str
    recommendations: List[RecommendationItem]


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_cost_recommendations(
    account_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get cost optimization recommendations

    - AWS Compute Optimizer rightsizing
    - Unattached EBS volumes
    - Old snapshots
    - Idle resources (low CPU usage)
    - Cost-based recommendations
    """
    from app.services.recommendations_service import RecommendationsService

    recommendations_service = RecommendationsService(db)

    # Get AWS account if specified
    aws_account = None
    if account_id:
        aws_account = db.query(AWSAccount).filter(
            AWSAccount.id == account_id,
            AWSAccount.tenant_id == current_tenant.id
        ).first()

        if not aws_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AWS account not found"
            )

    # Get all recommendations
    recommendations = await recommendations_service.get_all_recommendations(
        tenant_id=str(current_tenant.id),
        aws_account=aws_account
    )

    # Calculate total potential savings
    total_savings = sum(rec.get('potential_savings', 0) for rec in recommendations)

    return {
        "total_recommendations": len(recommendations),
        "total_potential_savings": round(total_savings, 2),
        "currency": "USD",
        "recommendations": recommendations
    }


class TagBreakdownItem(BaseModel):
    tag_value: str
    cost: float
    percentage: float


class TagBreakdownResponse(BaseModel):
    tag_key: str
    total_cost: float
    currency: str
    start_date: str
    end_date: str
    breakdown: List[TagBreakdownItem]


@router.get("/by-tags", response_model=TagBreakdownResponse)
async def get_cost_by_tags(
    tag_key: str = Query(..., description="Tag key to group by (e.g., 'Environment', 'Project')"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get cost breakdown by AWS resource tags

    - Groups costs by specified tag key
    - Defaults to last 30 days if no dates provided
    - Shows percentage breakdown
    """
    # Set default dates
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    cost_service = CostService(db)

    breakdown = await cost_service.get_cost_by_tags(
        tenant_id=str(current_tenant.id),
        start_date=start_date,
        end_date=end_date,
        tag_key=tag_key,
        aws_account_id=account_id
    )

    return breakdown


class MultiAccountItem(BaseModel):
    account_id: str
    account_name: str
    aws_account_id: str
    cost: float
    percentage: float
    region: str


class MultiAccountResponse(BaseModel):
    total_cost: float
    currency: str
    start_date: str
    end_date: str
    account_count: int
    accounts: List[MultiAccountItem]


@router.get("/multi-account", response_model=MultiAccountResponse)
async def get_multi_account_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get aggregated cost summary across all AWS accounts

    - Shows cost breakdown per account
    - Includes percentages of total spend
    - Defaults to last 30 days
    """
    # Set default dates
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    cost_service = CostService(db)

    summary = await cost_service.get_multi_account_summary(
        tenant_id=str(current_tenant.id),
        start_date=start_date,
        end_date=end_date
    )

    return summary


@router.get("/export/pdf")
async def export_costs_pdf(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Export cost report to PDF format

    - Generates comprehensive cost report
    - Includes charts and summaries
    - Returns PDF file for download
    """
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    import io

    # Set default dates
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Get cost data
    cost_service = CostService(db)

    summary = await cost_service.get_cost_summary(
        tenant_id=str(current_tenant.id),
        start_date=start_date,
        end_date=end_date,
        aws_account_id=account_id
    )

    trend = await cost_service.get_cost_trend(
        tenant_id=str(current_tenant.id),
        start_date=start_date,
        end_date=end_date,
        aws_account_id=account_id
    )

    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    # Title
    story.append(Paragraph("CloudCostly Cost Report", title_style))
    story.append(Spacer(1, 0.3*inch))

    # Report Info
    info_style = styles['Normal']
    story.append(Paragraph(f"<b>Report Period:</b> {start_date} to {end_date}", info_style))
    story.append(Paragraph(f"<b>Total Cost:</b> ${summary['total_cost']:.2f} {summary['currency']}", info_style))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
    story.append(Spacer(1, 0.5*inch))

    # Cost Summary Table
    story.append(Paragraph("<b>Cost Breakdown by Service</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    # Create table data
    table_data = [['Service', 'Cost', 'Percentage']]
    for item in summary['breakdown'][:10]:  # Top 10 services
        table_data.append([
            item['service'],
            f"${item['cost']:.2f}",
            f"{item['percentage']:.1f}%"
        ])

    # Create table
    table = Table(table_data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*inch))

    # Daily Trend
    story.append(Paragraph("<b>Daily Cost Trend</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    trend_data = [['Date', 'Cost']]
    for item in trend[-7:]:  # Last 7 days
        trend_data.append([item['date'], f"${item['cost']:.2f}"])

    trend_table = Table(trend_data, colWidths=[3.5*inch, 3*inch])
    trend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(trend_table)

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    filename = f"cloudcostly_report_{start_date}_{end_date}.pdf"

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
