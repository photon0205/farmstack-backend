from rest_framework.reverse import reverse
from django.test import Client, TestCase
from rest_framework import status
import json
from datahub.models import Organization, UserOrganizationMap
from accounts.models import User, UserRole
from participant.models import SupportTicketV2
from rest_framework_simplejwt.tokens import RefreshToken


auth_co_steward= {
    "token": "null"
}

auth_participant={
   "token": "null" 
}

# Generic method to create access token(admin/participant/co-steward)
def create_token_for_user(user, user_map):
    refresh_token = RefreshToken.for_user(user)
    refresh_token["org_id"] = str(user_map.organization_id) if user_map else None
    refresh_token["map_id"] = str(user_map.id) if user_map else None
    refresh_token["role"] = str(user.role_id)
    refresh_token["onboarded_by"] = str(user.on_boarded_by_id)
    refresh_token.access_token["org_id"] = str(user_map.organization_id) if user_map else None
    refresh_token.access_token["map_id"] = str(user_map.id) if user_map else None
    refresh_token.access_token["role"] = str(user.role_id)
    refresh_token.access_token["onboarded_by"] = str(user.on_boarded_by_id)

    return refresh_token.access_token

class  SupportTicketNewRequestTestCaseForViews(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.client_participant = Client()
        self.support_ticket_url = reverse("support_tickets-list")
        self.user_role_participant = UserRole.objects.create(id=3, role_name="datahub_participant_root")
        self.user_costeward_role = UserRole.objects.create(id=6, role_name="datahub_co_steward")
        self.user_participant = User.objects.create(
            email="akshata@digitalgreen.org",
            role_id=self.user_role_participant.id,
        )
        self.user_co_steward = User.objects.create(
            email="costeward@digitalgreen.org",
            role_id=self.user_costeward_role.id,
        )
        self.creating_org_participant = Organization.objects.create(
            org_email="participant@digitalgreen.org",
            name="Participant One",
            phone_number="5678909876",
            website="htttps://google.com",
            address=({"city": "Banglore"}),
        )
        self.creating_co_steward = Organization.objects.create(
            org_email="costewdardorg@digitalgreen.org",
            name="Co-steward",
            phone_number="1234567890",
            website="htttps://google.com",
            address=({"city": "Banglore"}),
        )
        self.user_co_steward_map=UserOrganizationMap.objects.create(user_id=self.user_co_steward.id, organization_id=self.creating_co_steward.id)
        self.user_map_participant=UserOrganizationMap.objects.create(user_id=self.user_participant.id, organization_id=self.creating_org_participant.id)


        # Access token for Co-steward
        auth_co_steward["token"] = create_token_for_user(self.user_co_steward, self.user_co_steward_map)
        co_steward_header=self.set_auth_headers(co_steward=True)
        self.client.defaults['HTTP_AUTHORIZATION'] = co_steward_header[0]
        self.client.defaults['CONTENT_TYPE'] = co_steward_header[1]


        # Access token for Participant
        auth_participant["token"] = create_token_for_user(self.user_participant, self.user_map_participant)
        participant_header=self.set_auth_headers(participant=True)
        self.client_participant.defaults['HTTP_AUTHORIZATION'] = participant_header[0]
        self.client_participant.defaults['CONTENT_TYPE'] = participant_header[1]


    #Generic function to return headers 
    def set_auth_headers(self,participant=False, co_steward=True):  
        auth_data = auth_participant if participant else auth_co_steward 
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_data["token"]}'
        }
        return headers['Authorization'],headers['Content-Type']
    
    # Positive test cases
    def test_ticket_creation_with_participant(self):
        data={
            "ticket_title":"Support ticket by participant",
            "category":"connectors",
            "description":"description about support ticket 1........",
            "status": "open",
            "user_map":str(self.user_map_participant.id)
          }
        response = self.client_participant.post(self.support_ticket_url, json.dumps(data), content_type='application/json')
        assert response.status_code == 201
        assert response.json()['ticket_title']==data["ticket_title"]
        assert response.json()['description']==data["description"]
        assert response.json()['category']==data["category"]
        

    def test_ticket_creation_with_co_steward(self):
        data={
            "ticket_title":"Support ticket by co-steward",
            "category":"connectors",
            "description":"description about support ticket..........",
            "status": "open",
            "user_map":str(self.user_co_steward_map.id) 
            }
        response = self.client.post(self.support_ticket_url, json.dumps(data), content_type='application/json')
        assert response.status_code == 201
        assert response.json()['ticket_title']==data["ticket_title"]
        assert response.json()['description']==data["description"]
        assert response.json()['category']==data["category"]


    # Negative test cases
    def test_ticket_creation_with_Invalid_token(self):
        data={
            "ticket_title":"Support ticket 1",
            "category":"connectors",
            "description":"description about support ticket 1",
            "status": "open",
            "user_map":str(self.user_map_participant)
          }
        response = self.client_participant.post(self.support_ticket_url, json.dumps(data), content_type='application/json')
        assert response.status_code == 401
        assert response.json()=={'message': 'Invalid auth credentials provided.'}


    def test_ticket_creation_with_empty_data(self):
        data={" "}
        response = self.client_participant.post(self.support_ticket_url, data, content_type='application/json')
        assert response.status_code == 401
        assert response.json()=={'message': 'Invalid auth credentials provided.'}


    


    
 