document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const staffLogin = document.getElementById("staff-login");
  const staffTools = document.getElementById("staff-tools");
  const staffMessage = document.getElementById("staff-message");
  const volunteerForm = document.getElementById("volunteer-form");
  const volunteerSelect = document.getElementById("volunteer-profile");
  const assignmentVolunteer = document.getElementById("assignment-volunteer");
  const assignmentActivity = document.getElementById("assignment-activity");
  let staffToken = "";
  let volunteers = [];

  function escapeHTML(value) {
    const element = document.createElement("span");
    element.textContent = value;
    return element.innerHTML.replaceAll('"', "&quot;").replaceAll("'", "&#39;");
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.querySelectorAll("option:not(:first-child)").forEach((option) => {
        option.remove();
      });
      const selectedAssignmentActivity = assignmentActivity.value;
      assignmentActivity.querySelectorAll("option:not(:first-child)").forEach((option) => {
        option.remove();
      });

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${escapeHTML(email)}</span><button class="delete-btn" data-activity="${escapeHTML(name)}" data-email="${escapeHTML(email)}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${escapeHTML(name)}</h4>
          <p>${escapeHTML(details.description)}</p>
          <p><strong>Schedule:</strong> ${escapeHTML(details.schedule)}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
          <div class="participants-container participants-section">
            <h5>Assigned Volunteers:</h5>
            ${details.volunteers.length
              ? `<ul>${details.volunteers.map((volunteer) =>
                `<li>${escapeHTML(volunteer.name)}</li>`).join("")}</ul>`
              : "<p>No volunteers assigned yet</p>"}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
        assignmentActivity.appendChild(option.cloneNode(true));
      });
      assignmentActivity.value = selectedAssignmentActivity;

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  function lockStaffTools() {
    staffToken = "";
    volunteers = [];
    staffLogin.reset();
    volunteerForm.reset();
    [volunteerSelect, assignmentVolunteer].forEach((select) => {
      select.querySelectorAll("option:not(:first-child)").forEach((option) => option.remove());
      select.value = "";
    });
    staffTools.classList.add("hidden");
    staffLogin.classList.remove("hidden");
  }

  async function staffRequest(path, method = "GET", body) {
    const requestToken = staffToken;
    const response = await fetch(path, {
      method,
      headers: {
        Authorization: "Bearer " + requestToken,
        "Content-Type": "application/json",
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
    const result = await response.json();
    if (staffToken !== requestToken) throw new Error("Staff tools are locked.");
    if (!response.ok) {
      if (response.status === 401 || response.status === 503) lockStaffTools();
      throw new Error(typeof result.detail === "string"
        ? result.detail : "Please check the volunteer profile fields.");
    }
    return result;
  }

  async function fetchVolunteers(selectedId = volunteerSelect.value) {
    volunteers = await staffRequest("/volunteers");
    [volunteerSelect, assignmentVolunteer].forEach((select) => {
      const previous = select.value;
      select.querySelectorAll("option:not(:first-child)").forEach((option) => option.remove());
      volunteers.forEach((volunteer) => {
        const option = document.createElement("option");
        option.value = volunteer.id;
        option.textContent = `${volunteer.name} (#${volunteer.id})`;
        select.appendChild(option);
      });
      select.value = previous;
    });
    volunteerSelect.value = selectedId;
  }

  staffLogin.addEventListener("submit", async (event) => {
    event.preventDefault();
    staffToken = document.getElementById("staff-token").value;
    try {
      await fetchVolunteers();
      staffLogin.reset();
      staffLogin.classList.add("hidden");
      staffTools.classList.remove("hidden");
      staffMessage.textContent = "Staff tools unlocked.";
    } catch (error) {
      lockStaffTools();
      staffMessage.textContent = error.message;
    }
  });

  document.getElementById("staff-logout").addEventListener("click", () => {
    lockStaffTools();
    staffMessage.textContent = "Staff tools locked.";
  });

  volunteerSelect.addEventListener("change", () => {
    volunteerForm.reset();
    const volunteer = volunteers.find((item) => String(item.id) === volunteerSelect.value);
    if (volunteer) {
      Array.from(volunteerForm.elements).filter((input) => input.name).forEach((input) => {
        if (input.type === "checkbox") input.checked = volunteer[input.name];
        else input.value = volunteer[input.name];
      });
    }
  });

  volunteerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const profile = {};
    Array.from(volunteerForm.elements).filter((input) => input.name).forEach((input) => {
      profile[input.name] = input.type === "checkbox" ? input.checked : input.value;
    });
    const id = volunteerSelect.value;
    try {
      const saved = await staffRequest(id ? `/volunteers/${id}` : "/volunteers",
        id ? "PUT" : "POST", profile);
      await fetchVolunteers(String(saved.id));
      await fetchActivities();
      staffMessage.textContent = "Volunteer profile saved.";
    } catch (error) {
      staffMessage.textContent = error.message;
    }
  });

  document.getElementById("assignment-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const result = await staffRequest(
        `/activities/${encodeURIComponent(assignmentActivity.value)}/volunteers/${assignmentVolunteer.value}`,
        event.submitter?.value || "PUT"
      );
      await fetchActivities();
      staffMessage.textContent = result.message;
    } catch (error) {
      staffMessage.textContent = error.message;
    }
  });

  // Initialize app
  fetchActivities();
});
