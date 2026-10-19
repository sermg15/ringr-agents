import pytest
from datetime import timedelta

from django.test import Client
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from calls.models import Call, CallResult, Campaign, CampaignOwnership, Contact, ScriptStep, Tenant

pytestmark = pytest.mark.django_db


@pytest.fixture
def call() -> Call:
    tenant = Tenant.objects.create(name='acme')
    campaign = Campaign.objects.create(name='acme collections')
    CampaignOwnership.objects.create(campaign=campaign, tenant=tenant)
    ScriptStep.objects.create(campaign=campaign, order=1, text='Greet the contact.')
    contact = Contact.objects.create(name='Lucia Garcia', phone='+34600000001')
    return Call.objects.create(campaign=campaign, contact=contact)


def test_context_has_the_expected_shape(client: Client, call: Call) -> None:
    body = client.get(f'/calls/{call.id}/context').json()

    assert body == {
        'call_id': str(call.id),
        'tenant': {'id': call.campaign.ownerships.get().tenant_id},
        'contact': {'name': 'Lucia Garcia', 'phone': '+34600000001'},
        'script': [{'order': 1, 'text': 'Greet the contact.'}],
        'history': [],
    }


def test_result_is_stored(client: Client, call: Call) -> None:
    response = client.post(
        f'/calls/{call.id}/result',
        {'outcome': 'completed', 'duration_s': 95.0, 'transcript': 'user: Hello'},
        content_type='application/json',
    )

    assert response.status_code == 200
    assert CallResult.objects.get(call=call).outcome == 'completed'

def test_queries_historical_calls(client: Client, call: Call) -> None:
    with CaptureQueriesContext(connection) as queries_without_history:
        response = client.get(f'/calls/{call.id}/context')

    assert response.status_code == 200

    for days_ago in range(20):
        previous_call = Call.objects.create(
            campaign=call.campaign,
            contact=call.contact,
            status=Call.Status.FINISHED,
            created_at=timezone.now() - timedelta(days=days_ago + 1),
        )
        CallResult.objects.create(
            call=previous_call,
            outcome=CallResult.Outcome.COMPLETED,
            duration_s=60,
            transcript='Previous call',
        )

    with CaptureQueriesContext(connection) as queries_with_history:
        response = client.get(f'/calls/{call.id}/context')

    assert response.status_code == 200
    assert len(response.json()['history']) == 20
    assert len(queries_with_history) <= len(queries_without_history) + 2