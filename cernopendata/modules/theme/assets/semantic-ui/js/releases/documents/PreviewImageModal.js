import React from "react";
import { Modal, Image, Divider, Button, Icon } from "semantic-ui-react";

export default function PreviewImageModal({ image, onClose }) {
  return (
    <Modal open={!!image} onClose={onClose} closeIcon size="large">
      <Modal.Header>{image?.filename}</Modal.Header>
      <Modal.Content>
        {image && (
          <>
            <Image src={image.url} alt={image.filename} centered />
            <Divider hidden />
            <strong>Body snippet</strong>
            <div className="image-snippet-row">
              <pre className="image-snippet-code">{`<img src="${image.url}">`}</pre>
              <Button
                size="small"
                onClick={() =>
                  navigator.clipboard.writeText(`<img src="${image.url}">`)
                }
              >
                <Icon name="copy outline" /> Copy snippet
              </Button>
            </div>
          </>
        )}
      </Modal.Content>
    </Modal>
  );
}
