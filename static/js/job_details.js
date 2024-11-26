


function displayJobDetails(data) {
    // Titre du poste
    if (data.formatted_text) {
        const sections = data.formatted_text.split('\n\n');
        let currentSection = '';

        sections.forEach(section => {
            /* if (section.toLowerCase().includes('titre poste')) {
                document.getElementById('jobTitle').textContent = section;
            } else */

             if (section.toLowerCase().includes('description')) {
                document.getElementById('formattedJobDescription').innerHTML = `<pre>${section}</pre>`;
            } else if (section.toLowerCase().includes('requirements')) {
                addToList('formattedRequirements', section);
            } else if (section.toLowerCase().includes('skills')) {
                addToList('formattedSkills', section);
            } else if (section.toLowerCase().includes('autres')) {
                document.getElementById('formattedAdditional').innerHTML = `<pre>${section}</pre>`;
            }
        });
    }
}

function addToList(elementId, text) {
    const ul = document.getElementById(elementId);
    const lines = text.split('\n');
    lines.forEach((line, index) => {
        if (index > 0 && line.trim()) { // Skip header line
            const li = document.createElement('li');
            li.textContent = line.trim();
            ul.appendChild(li);
        }
    });
}