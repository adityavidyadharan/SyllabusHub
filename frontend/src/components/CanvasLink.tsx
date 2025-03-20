import { Button, Container, Row } from "react-bootstrap";
import { Check } from "react-bootstrap-icons";
import CanvasSync from "./CanvasSync";

export default function CanvasLink() {
    return (
        <Container className="text-center mb-3">
            <Row className="text-center align-items-center mb-3">
                <span>
                    Canvas Account Link:  <Check size={20} color="green" />
                </span>
            </Row>
            <Row>
                <CanvasSync />
            </Row>
        </Container>
    )
}