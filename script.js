document.addEventListener('DOMContentLoaded', () => {
    const itemForm = document.getElementById('item-form');
    const baseUrl = 'http://localhost:8000'; // URL OF UVICORN
    const submitButton = document.querySelector('button[type="submit"]');
    const itemsTableBody = document.getElementById('items-table').getElementsByTagName('tbody')[0];
    const deleteSelectedButton = document.getElementById('delete-selected');

    itemForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(itemForm);
        const itemId = formData.get('item_id') || null;
        const itemName = formData.get('name');
        const item = {
            name: itemName,
            description: formData.get('description'),
            price: parseFloat(formData.get('price')),
            tax: parseFloat(formData.get('tax')) || 0
        };

        // Indicate loading state
        submitButton.textContent = 'Processing...';
        submitButton.disabled = true;

        try {
            const existingItems = await fetch(`${baseUrl}/items/`);
            if (!existingItems.ok) {
                throw new Error(`HTTP error! Status: ${existingItems.status}`);
            }
            const items = await existingItems.json();
            const existingItem = items.find(i => i.item.name == itemName);
            

            let response;
            if (existingItem) {

                // Update item
                response = await fetch(`${baseUrl}/items/${existingItem.item_id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(item),
                    mode: 'cors'
                });
            } else {
                // Insert item
                response = await fetch(`${baseUrl}/items/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(item),
                    mode: 'cors'
                });
            }
            
            const result = await response.json();
            alert(result.message || 'Operation successful');
            itemForm.reset();

            fetchItems();

            submitButton.textContent = 'Submit Item';
            submitButton.disabled = false;
        } catch (error) {
            console.error('Error:', error);
            alert(`An error occurred: ${error.message}`);
        }
    });

    async function fetchItems() {
        // Indicate loading state
        itemsTableBody.innerHTML = '<tr><td colspan="7">Loading...</td></tr>';

        try {
            const response = await fetch(`${baseUrl}/items/`);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const items = await response.json();
            displayItems(items);
        } catch (error) {
            console.error('Error fetching items:', error);
            alert(`Failed to fetch items: ${error.message}`);
            itemsTableBody.innerHTML = '<tr><td colspan="7">Failed to load items.</td></tr>';
        }
    }

    function displayItems(items) {
        itemsTableBody.innerHTML = '';
        items.forEach(item => {
            const row = itemsTableBody.insertRow();
            const checkboxCell = row.insertCell();
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = item.item_id;
            checkboxCell.appendChild(checkbox);

            row.insertCell().textContent = item.item_id;
            row.insertCell().textContent = item.item.name;
            row.insertCell().textContent = item.item.description || 'N/A';
            row.insertCell().textContent = item.item.price.toFixed(2);
            row.insertCell().textContent = item.item.tax.toFixed(2);
        });
    }

    deleteSelectedButton.addEventListener('click', async () => {
        const selectedCheckboxes = document.querySelectorAll('input[type="checkbox"]:checked');
        if (selectedCheckboxes.length === 0) {
            alert('No items selected for deletion.');
            return;
        }
        
        const idsToDelete = Array.from(selectedCheckboxes).map(checkbox => checkbox.value);
        if (confirm(`Are you sure you want to delete ${idsToDelete.length} item(s)?`)) {
            try {
                await Promise.all(idsToDelete.map(id => fetch(`${baseUrl}/items/${id}`, { method: 'DELETE' })));
                alert('Selected items deleted successfully.');
                fetchItems();
            } catch (error) {
                console.error('Error deleting items:', error);
                alert(`Failed to delete items: ${error.message}`);
            }
        }
    });

    fetchItems();
});
