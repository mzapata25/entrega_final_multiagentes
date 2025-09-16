using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;

[System.Serializable]
public class AgentData
{
    public int id;
    public int x;
    public int y;
    public bool has_food;
}

[System.Serializable]
public class PositionData
{
    public int x;
    public int y;
}

[System.Serializable]
public class SimulationState
{
    public bool is_finished;
    public List<AgentData> agents;
    public List<PositionData> food;
}

public class SimulationManager : MonoBehaviour
{
    public GameObject agentPrefab;
    public GameObject foodPrefab;
    public GameObject basePrefab;

    private string serverUrl = "http://localhost:5000";
    public float updateInterval = 0.2f;

    private Dictionary<int, GameObject> agentObjects = new Dictionary<int, GameObject>();
    private List<GameObject> foodObjects = new List<GameObject>();

    void Start()
    {
        Instantiate(basePrefab, new Vector3(5, 0.3f, 5), Quaternion.identity);
        StartCoroutine(GetSimulationData());
    }


    IEnumerator GetSimulationData()
    {
        while (true)
        {
            using (UnityWebRequest request = UnityWebRequest.Get(serverUrl + "/step"))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    string jsonResponse = request.downloadHandler.text;
                    SimulationState state = JsonUtility.FromJson<SimulationState>(jsonResponse);
                    
                    UpdateScene(state);

                    if (state.is_finished)
                    {
                        Debug.Log("¡Simulación terminada! No se pedirán más pasos.");
                        break;
                    }
                }
                else
                {
                    Debug.LogError("Error en el servidor: " + request.error);
                    break;
                }
            }
            yield return new WaitForSeconds(updateInterval);
        }
    }

    void UpdateScene(SimulationState state)
    {
        foreach (var agentData in state.agents)
        {
            Vector3 position = new Vector3(agentData.x, 0.5f, agentData.y);
            
            if (agentObjects.ContainsKey(agentData.id))
            {
                agentObjects[agentData.id].transform.position = position;
            }
            else
            {
                GameObject newAgent = Instantiate(agentPrefab, position, Quaternion.identity);
                agentObjects.Add(agentData.id, newAgent);
            }
            
            Material agentMaterial = agentObjects[agentData.id].GetComponent<Renderer>().material;
            agentMaterial.color = agentData.has_food ? Color.yellow : Color.green;
        }

        foreach (var foodObject in foodObjects)
        {
            Destroy(foodObject);
        }
        foodObjects.Clear();

        foreach (var foodData in state.food)
        {
            Vector3 position = new Vector3(foodData.x, 0.25f, foodData.y);
            GameObject newFood = Instantiate(foodPrefab, position, Quaternion.identity);
            foodObjects.Add(newFood);
        }
    }
}