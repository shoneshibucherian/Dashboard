"""Unit tests for the Flask app in modified_serve.py using pytest and mongomock."""
from datetime import datetime
import pytest
import mongomock
from modified_serve import app



# pylint: disable=unused-argument,redefined-outer-name
def patched_handle_date_operator(self, operator, values):
    """Handle $dateFromString operator in aggregation pipeline 
    which has not been implemented in mongomock.
    Parameters
    ----------
    operator : str
        The date operator, e.g., "$dateFromString".
    values : dict
        The values associated with the operator.


    Returns
    -------
    datetime
        The converted datetime object.


    Raises
    ------
    ValueError
        If the date string is invalid or missing.   
    
    """
    if operator == "$dateFromString":
        if isinstance(values, dict) and "dateString" in values:
            date_str = values["dateString"]
            # If date_str is a field reference, resolve it
            if isinstance(date_str, str) and date_str.startswith("$"):
                # Remove the '$' and get the value from the document
                field_name = date_str[1:]
                document = getattr(self, "_doc_dict", {})
                date_str = document.get(field_name)

            if isinstance(date_str, str) and date_str:
                try:
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except Exception as e:
                    raise ValueError(f"Invalid date string for $dateFromString: {date_str}") from e
        raise ValueError(f"Missing or invalid dateString for $dateFromString: {values}")
    return original_handle_date_operator(self, operator, values)
# Save the original method
ParserCls = getattr(mongomock.aggregate, "_Parser")
original_handle_date_operator = getattr(ParserCls, "_handle_date_operator")
setattr(ParserCls, "_handle_date_operator", patched_handle_date_operator)

# original_handle_date_operator = mongomock.aggregate._Parser._handle_date_operator
# # Patch it
# mongomock.aggregate._Parser._handle_date_operator = patched_handle_date_operator



# --- Fixtures ---

@pytest.fixture
def client():
    """Provide a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as app_client:
        yield app_client

@pytest.fixture
def mock_collection(monkeypatch):
    """Provide an in-memory MongoDB collection using mongomock."""
    client = mongomock.MongoClient()
    db = client["test_db"]
    collection = db["test_collection"]

    # Insert sample documents
    collection.insert_many([
        #duration=0.2, all keys=123, date=2025-06-13
        #(for key: should be filtered out by duration>0.1)
        {
            "_id": {
                "$oid": "689b6039e9764468992076786781"
            },
            "timestamp": "2025-06-13T22:07:22.860590Z",
            "mb_values": [
                12.17,
                17.66,
                9.38,
                8.84,
                46.68,
                49.12,
                31.9,
                26.84
            ],
            "mb_start_bw": 46.68,
            "max_bandwidth": 49.12,
            "ms_interval": 25,
            "duration_sec": 0.25,
            "key": {
                "switch": 123,
                "port": 123,
                "queue": 123,
                "vlan_id": 0
            }
        },
        #duration=0.07, vlan=333, date=2025-06-15
        #(for vlan: should be filtered out by duration>0.1)
        {
            "_id": {
                "$oid": "689b6039e976446899207567871"
            },
            "timestamp": "2025-06-15T22:07:22.860590Z",
            "mb_values": [
                12.17,
                17.66,
                9.38,
                8.84,
                46.68,
                49.12,
                31.9,
                26.84
            ],
            "mb_start_bw": 46.68,
            "max_bandwidth": 49.12,
            "ms_interval": 25,
            "duration_sec": 0.0015245,
            "key": {
                "switch": 262146,
                "port": 17,
                "queue": 0,
                "vlan_id": 333
            }
        },
        #duration=3, vlan=444, date=2025-06-14
        #(for vlan: should PASS filter (>2))
        {
            "_id": {
                "$oid": "689b6039e967871"
            },
            "timestamp": "2025-06-14T22:07:22.860590Z",
            "mb_values": [
                12.17,
                17.66,
                9.38,
                8.84,
                46.68,
                49.12,
                31.9,
                26.84
            ],
            "mb_start_bw": 46.68,
            "max_bandwidth": 49.12,
            "ms_interval": 25,
            "duration_sec": 0.003254,
            "key": {
                "switch": 262146,
                "port": 17,
                "queue": 0,
                "vlan_id": 444
            }
        },
        #duration=0.025, all keys=18, date=2025-06-13
        #(for key: should be filtered out by mb_start_bw>60)
        {
            "timestamp": "2025-06-13T22:07:22.860590Z",
            "duration_sec": 0.02503,   
            "max_bandwidth": 36.46,
            "mb_start_bw": 80.00,
            "key": {"switch": 18, "port": 18, "queue": 18, "vlan_id": 0}
        },
        #duration=0.07, all keys=111, date=2025-06-14
        #(for key: should PASS filter (==0.1))
        {
            "timestamp": '2025-06-14T22:07:22.860590Z',
            "duration_sec": 0.07,      # should PASS filter (==0.1)
            "max_bandwidth": 10,
            "mb_start_bw": 40.00,
            "key": {"switch": 111, "port": 111, "queue": 111, "vlan_id": 0}
        },
        #duration=0.1, all keys=5555, date=2025-06-14
        #(for key: should PASS filter (==0.1))
        {
            "timestamp": '2025-06-14T22:07:22.860590Z',
            "duration_sec": 0.001,      # should PASS filter (==0.1)
            "max_bandwidth": 10,
            "mb_start_bw": 40.00,
            "key": {"switch": 5555, "port": 5555, "queue": 5555, "vlan_id": 0}
        },
        # Four documents for time_of_day test, each in a different time segment
        #early_morning
        {
            "timestamp": '2025-06-18T03:07:22.860590Z',
            "duration_sec": 0.33,      
            "max_bandwidth": 10,
            "mb_start_bw": 40.00,
            "key": {"switch": 00, "port": 00, "queue": 00, "vlan_id": 00}
        },
        #morning
        {
            "timestamp": '2025-06-18T08:07:22.860590Z',
            "duration_sec": 0.33,      
            "max_bandwidth": 10,
            "mb_start_bw": 40.00,
            "key": {"switch": 00, "port": 00, "queue": 00, "vlan_id": 00}
        },
        #afternoon
        {
            "timestamp": '2025-06-18T13:07:22.860590Z',
            "duration_sec": 0.33,      
            "max_bandwidth": 10,
            "mb_start_bw": 40.00,
            "key": {"switch": 00, "port": 00, "queue": 00, "vlan_id": 00}
        },
        #evening
        {
            "timestamp": '2025-06-18T20:07:22.860590Z',
            "duration_sec": 0.33,      
            "max_bandwidth": 10,
            "mb_start_bw": 40.00,
            "key": {"switch": 00, "port": 00, "queue": 00, "vlan_id": 00}
        }
    ])

    # Patch the collection in tests
    # mocker.patch("modified_serve.collection", collection)
    # return collection
    monkeypatch.setattr("modified_serve.collection", collection)
    return collection


# --- Tests ---

def test_key_show_filters(client, mock_collection):
    """Test that /key_show only returns docs with duration_sec > 0.1."""


    #this checks if there is a docuement in the db with duration==0.1
    #if that is the case, then the key has to be=switch:5555, port:5555, queue:5555
    response_duration_eq_0_1 = client.get(
        "/key_show?duration==1&from=1749045197072&max_band=&phy=All" \
        "&time=1d&to=1756821197072&start_band=&vlan=All"      
    )
    assert response_duration_eq_0_1.status_code == 200
    data = response_duration_eq_0_1.get_json()

    assert data[0]["key"] == "switch:5555, port: 5555, queue: 5555"

    #this checks if there is a docuement in the db where all the key values are 111
    response_all_key_eq_111 = client.get(
        "/key_show?duration=&from=1749045197072&max_band=&phy=switch:111,+port:111,+queue:111" \
        "&time=1d&to=1756821197072&start_band=&vlan=All"
    )
    assert response_all_key_eq_111.status_code == 200
    data = response_all_key_eq_111.get_json()
    assert data[0]["key"] == "switch:111, port: 111, queue: 111"

    #this checks if there is a docuement in the db where all start_band>60
    #since the only document that has mb_start_bw>60 is the one with all keys=18
    response_all_key_eq_111 = client.get(
        "/key_show?duration=&from=1749045197072&max_band=&phy=All" \
        "&time=1d&to=1756821197072&start_band=>=60&vlan=All"
    )
    assert response_all_key_eq_111.status_code == 200
    data = response_all_key_eq_111.get_json()
    assert data[0]["key"] == "switch:18, port: 18, queue: 18"



def test_vlan_show_filters(client, mock_collection):
    """Test that /vlan_show respects vlan_id != 0 condition."""


    #this checks if there is a docuement in the db where vlan_id=333
    response_vlan_eq_333 = client.get(
        "/vlan_show?duration=&from=1749045197072&max_band=&phy=All&" \
        "time=1d&to=1756821197072&start_band=&vlan=333"
    )
    assert response_vlan_eq_333.status_code == 200
    data = response_vlan_eq_333.get_json()
    assert data[0]["vlan"]=='vlan_id:333'

    #this checks if there is a docuement in the db where duration=2
    response_duration_gt_3 = client.get(
        "/vlan_show?duration=>3&from=1749045197072&max_band=&" \
        "phy=All&time=1d&to=1756821197072&start_band=&vlan=All"
    )
    assert response_duration_gt_3.status_code == 200
    data = response_duration_gt_3.get_json()
    assert data[0]["vlan"]=='vlan_id:444'


def test_time_of_day_filters(client, mock_collection):
    """Test that /time_of_day, targeting at the specific four documents 
    in mock_collection where each timestamp falls under a different time of day segment."""

    response = client.get(
        "/time_of_day?duration=&end=2025-07-08&from=1750118400000&max_band=&" \
        "phy=All&start=2025-06-24&start_band=&to=1750377599000&vlan=All"
    )
    assert response.status_code == 200
    data = response.get_json()
    # There should be exactly one aggregated result for the date 2025-06-18
    assert data[0]=={'afternoon': 1, 'date': '2025-06-18', 'early_morning': 1,
                      'evening': 1, 'morning': 1}


def test_bandwidth_vs_time(client, mock_collection):
    """Test the bandwidth_vs_time route returns correct fields."""
    response = client.get("/bandwidth_vs_time")
    assert response.status_code == 200
    data = response.get_json()

    assert all("_value" in d and "_time" in d for d in data)


def test_ping(client):
    """Sanity check for ping route."""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.get_json() == {"result": 200}
