function getCourseList() {
    return fetch("/api/courses")
        .then((response) => response.json())
        .then((data) => data.courses);
}