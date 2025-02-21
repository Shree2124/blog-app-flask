console.log("Hello");

function like(postId) {
    const likeCount = document.getElementById(`likes-count-${postId}`);
    const likeButton = document.getElementById(`like-button-${postId}`);

    fetch(`/like-post/${postId}`, { method: "POST" })
        .then((res) => res.json())
        .then((data) => {
            if (data.error) {
                alert(data.error);
                return;
            }
            likeCount.innerText = data.likes;
            likeButton.classList.toggle("fas", data.liked);
            likeButton.classList.toggle("far", !data.liked);
        })
        .catch((e) => {
            console.error(e);
            alert("Could not like post.");
        });
}
